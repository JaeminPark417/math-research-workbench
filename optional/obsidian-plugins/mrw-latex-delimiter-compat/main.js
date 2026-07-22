const {
  Plugin,
  MarkdownRenderer,
  renderMath,
  finishRenderMath,
  editorLivePreviewField
} = require("obsidian");
const { StateField, RangeSetBuilder } = require("@codemirror/state");
const { Decoration, EditorView, ViewPlugin, WidgetType } = require("@codemirror/view");

const SKIP_SELECTOR = [
  "code",
  "pre",
  "script",
  "style",
  "textarea",
  "mjx-container",
  ".math",
  ".math-inline",
  ".math-block",
  ".katex",
  ".cm-editor"
].join(",");

const TABLE_WIDGET_SELECTOR = ".cm-table-widget";
const PROJECTION_GAP = "\u0000";
const COMMONMARK_ESCAPABLE = new Set(
  Array.from("!\"#$%&'()*+,-./:;<=>?@[\\]^_\x60{|}~")
);

module.exports = class LatexDelimiterCompatPlugin extends Plugin {
  onload() {
    initializeTableCellRetries(this);
    this.registerEditorExtension(createLivePreviewExtensions());

    this.registerMarkdownPostProcessor(async (el, ctx) => {
      if (el.dataset.latexDelimiterCompat === "rendered") return;

      const tableCellHandled = renderTableCellFromEditorSource(this, el, ctx);
      if (tableCellHandled) return;

      const sourceChanged = await renderSectionFromSource(this, el, ctx);
      if (sourceChanged) return;

      const fallbackChanged = renderLegacyMathDelimiters(el);
      if (fallbackChanged) {
        await finishRenderMath();
      }
    }, 1000);
  }
};

let finishMathScheduled = false;

class LegacyMathWidget extends WidgetType {
  constructor(source, display, raw, block) {
    super();
    this.source = source;
    this.display = display;
    this.raw = raw;
    this.block = block;
  }

  eq(other) {
    return (
      other instanceof LegacyMathWidget &&
      this.source === other.source &&
      this.display === other.display &&
      this.block === other.block
    );
  }

  toDOM(view) {
    const doc = view?.dom?.ownerDocument || document;
    const container = doc.createElement(this.block ? "div" : "span");
    container.className = this.block
      ? "latex-delimiter-compat-display"
      : this.display
        ? "latex-delimiter-compat-display-inline"
        : "latex-delimiter-compat-inline";

    try {
      container.appendChild(renderMath(this.source, this.display));
      scheduleFinishRenderMath();
    } catch (error) {
      container.textContent = this.raw;
    }

    return container;
  }

  ignoreEvent() {
    return false;
  }
}

function createLivePreviewExtensions() {
  const mathRangesField = StateField.define({
    create(state) {
      return findLegacyMathRanges(state.doc.toString());
    },
    update(ranges, transaction) {
      return transaction.docChanged
        ? findLegacyMathRanges(transaction.state.doc.toString())
        : ranges;
    }
  });

  const structuralMathField = StateField.define({
    create(state) {
      return buildStructuralMathDecorations(state, mathRangesField);
    },
    update(decorations, transaction) {
      const modeChanged =
        isLivePreview(transaction.startState) !== isLivePreview(transaction.state);

      if (transaction.docChanged || transaction.selection || modeChanged) {
        return buildStructuralMathDecorations(transaction.state, mathRangesField);
      }

      return decorations;
    },
    provide(field) {
      return EditorView.decorations.from(field);
    }
  });

  const inlineMathPlugin = ViewPlugin.fromClass(
    class {
      constructor(view) {
        this.decorations = buildInlineMathDecorations(view, mathRangesField);
      }

      update(update) {
        const modeChanged =
          isLivePreview(update.startState) !== isLivePreview(update.state);

        if (
          update.docChanged ||
          update.selectionSet ||
          update.viewportChanged ||
          modeChanged
        ) {
          this.decorations = buildInlineMathDecorations(update.view, mathRangesField);
        }
      }
    },
    {
      decorations(value) {
        return value.decorations;
      }
    }
  );

  const theme = EditorView.baseTheme({
    ".latex-delimiter-compat-inline": {
      display: "inline-block"
    },
    ".latex-delimiter-compat-display": {
      display: "block",
      overflowX: "auto",
      textAlign: "center",
      width: "100%"
    },
    ".latex-delimiter-compat-display-inline": {
      display: "inline-block",
      maxWidth: "100%",
      verticalAlign: "middle"
    }
  });

  return [mathRangesField, structuralMathField, inlineMathPlugin, theme];
}

function buildStructuralMathDecorations(state, mathRangesField) {
  if (!isLivePreview(state)) return Decoration.none;

  const builder = new RangeSetBuilder();
  const ranges = state.field(mathRangesField);

  for (const range of ranges) {
    if (!range.display && !range.multilineInline) continue;

    const decorationRange = range.display
      ? normalizeDisplayRange(state.doc, range)
      : { from: range.from, to: range.to, block: false };
    if (selectionOverlapsRange(state.selection, decorationRange.from, decorationRange.to)) {
      continue;
    }

    builder.add(
      decorationRange.from,
      decorationRange.to,
      Decoration.replace({
        block: decorationRange.block,
        widget: new LegacyMathWidget(
          range.source.trim(),
          range.display,
          range.raw,
          decorationRange.block
        )
      })
    );
  }

  return builder.finish();
}

function buildInlineMathDecorations(view, mathRangesField) {
  if (!isLivePreview(view.state)) return Decoration.none;

  const builder = new RangeSetBuilder();
  const ranges = view.state.field(mathRangesField);

  for (const range of ranges) {
    if (
      range.display ||
      range.multilineInline ||
      !rangeIntersectsViewport(range, view.visibleRanges)
    ) {
      continue;
    }
    if (selectionOverlapsRange(view.state.selection, range.from, range.to)) continue;

    builder.add(
      range.from,
      range.to,
      Decoration.replace({
        widget: new LegacyMathWidget(range.source.trim(), false, range.raw, false)
      })
    );
  }

  return builder.finish();
}

function normalizeDisplayRange(doc, range) {
  const startLine = doc.lineAt(range.from);
  const endLine = doc.lineAt(Math.max(range.from, range.to - 1));
  const before = doc.sliceString(startLine.from, range.from);
  const after = doc.sliceString(range.to, endLine.to);
  const block = /^\s*$/.test(before) && /^\s*$/.test(after);

  return block
    ? { from: startLine.from, to: endLine.to, block: true }
    : { from: range.from, to: range.to, block: false };
}

function rangeIntersectsViewport(range, visibleRanges) {
  return visibleRanges.some(({ from, to }) => range.from <= to && range.to >= from);
}

function selectionOverlapsRange(selection, from, to) {
  return selection.ranges.some((range) => range.from <= to && range.to >= from);
}

function isLivePreview(state) {
  if (!editorLivePreviewField) return false;
  return Boolean(state.field(editorLivePreviewField, false));
}

function scheduleFinishRenderMath() {
  if (finishMathScheduled) return;
  finishMathScheduled = true;

  queueMicrotask(() => {
    finishMathScheduled = false;
    try {
      const result = finishRenderMath();
      if (result && typeof result.catch === "function") {
        result.catch(() => {});
      }
    } catch (error) {
      // Keep the rendered widget visible even if finalization fails.
    }
  });
}

function initializeTableCellRetries(plugin) {
  plugin.pendingTableCells = new WeakSet();
  plugin.tableCellRetryHandles = new Set();
  plugin.tableCellRetriesActive = true;

  plugin.register(() => {
    plugin.tableCellRetriesActive = false;
    for (const handle of plugin.tableCellRetryHandles) {
      try {
        handle.cancel();
      } catch (error) {
        // The frame may already have been discarded with its document.
      }
    }
    plugin.tableCellRetryHandles.clear();
    plugin.pendingTableCells = new WeakSet();
  });
}

function renderTableCellFromEditorSource(plugin, el, ctx, allowDefer = true) {
  const widget = findTableWidget(ctx);
  if (!widget || typeof EditorView.findFromDOM !== "function") return false;

  const cell = el.closest?.("th,td");
  const table = cell?.closest?.("table");
  const row = cell?.parentElement;
  if (!cell || !table || !row) return false;

  const tableIsAttached = widget.contains(table);
  if (!tableIsAttached) {
    if (!allowDefer) return false;
    scheduleTableCellRetry(plugin, el, ctx);
    return true;
  }

  const domRows = Array.from(table.rows || []);
  const rowIndex = domRows.indexOf(row);
  const columnIndex = Array.from(row.cells || []).indexOf(cell);
  if (rowIndex < 0 || columnIndex < 0 || domRows.length === 0) return false;

  const columnCount = domRows[0].cells.length;
  if (
    columnCount === 0 ||
    domRows.some((domRow) => domRow.cells.length !== columnCount)
  ) {
    return false;
  }

  let rawCell = findRawTableCellSource(
    widget,
    rowIndex,
    columnIndex,
    domRows.length,
    columnCount
  );
  if (rawCell === null) {
    const view = findOuterEditorView(widget);
    if (!view) {
      if (!allowDefer) return false;
      scheduleTableCellRetry(plugin, el, ctx);
      return true;
    }

    const tableData = findTableDataForWidget(
      view,
      widget,
      domRows.length,
      columnCount
    );
    rawCell = tableData?.rows?.[rowIndex]?.[columnIndex] ?? null;
  }
  if (typeof rawCell !== "string" || !hasLegacyMathDelimiter(rawCell)) {
    return false;
  }

  const mathRanges = findLegacyMathRanges(rawCell);
  if (mathRanges.length === 0) return false;

  const changed = replaceProjectedMath(el, mathRanges);
  if (changed) scheduleFinishRenderMath();
  return changed;
}

function scheduleTableCellRetry(plugin, el, ctx) {
  if (
    !plugin.tableCellRetriesActive ||
    plugin.pendingTableCells.has(el)
  ) {
    return;
  }

  plugin.pendingTableCells.add(el);
  const win = el.ownerDocument?.defaultView;
  let handle;

  const retry = () => {
    plugin.tableCellRetryHandles.delete(handle);
    plugin.pendingTableCells.delete(el);
    const widget = findTableWidget(ctx);
    if (
      !plugin.tableCellRetriesActive ||
      !widget ||
      !widget.contains(el)
    ) {
      return;
    }
    renderTableCellFromEditorSource(plugin, el, ctx, false);
  };

  if (win && typeof win.requestAnimationFrame === "function") {
    const frameId = win.requestAnimationFrame(retry);
    handle = {
      cancel() {
        win.cancelAnimationFrame(frameId);
      }
    };
  } else {
    const timerId = setTimeout(retry, 0);
    handle = {
      cancel() {
        clearTimeout(timerId);
      }
    };
  }

  plugin.tableCellRetryHandles.add(handle);
}

function findOuterEditorView(widget) {
  const outerEditor = widget.closest?.(".cm-editor");

  try {
    return EditorView.findFromDOM(outerEditor || widget);
  } catch (error) {
    return null;
  }
}

function findTableWidget(ctx) {
  const container = ctx?.containerEl;
  if (!container) return null;
  if (container.matches?.(TABLE_WIDGET_SELECTOR)) return container;
  return container.closest?.(TABLE_WIDGET_SELECTOR) || null;
}

function findRawTableCellSource(
  widget,
  rowIndex,
  columnIndex,
  rowCount,
  columnCount
) {
  const coreWidget = widget?.cmView?.widget;
  if (
    !coreWidget ||
    coreWidget.containerEl !== widget ||
    !Array.isArray(coreWidget.rows) ||
    coreWidget.rows.length !== rowCount ||
    coreWidget.rows.some(
      (row) => !Array.isArray(row) || row.length !== columnCount
    )
  ) {
    return null;
  }

  const coreCell = coreWidget.rows[rowIndex]?.[columnIndex];
  return typeof coreCell?.text === "string" ? coreCell.text : null;
}

function findTableDataForWidget(view, widget, rowCount, columnCount) {
  const doc = view?.state?.doc;
  if (
    !doc ||
    typeof doc.sliceString !== "function" ||
    !Number.isInteger(doc.length)
  ) {
    return null;
  }

  const positions = findWidgetDocumentPositions(view, widget, doc.length);
  if (positions.length === 0) return null;

  const directCandidates = new Map();
  if (typeof view.lineBlockAt === "function") {
    for (const position of positions) {
      try {
        const block = view.lineBlockAt(position);
        const parsed = parseTableCandidate(
          doc.sliceString(block.from, block.to),
          rowCount,
          columnCount
        );
        if (parsed) {
          directCandidates.set(JSON.stringify(parsed.rows), parsed);
        }
      } catch (error) {
        // Fall through to the bounded line scan below.
      }
    }
  }

  if (directCandidates.size === 1) {
    return directCandidates.values().next().value;
  }
  if (directCandidates.size > 1) return null;

  if (
    typeof doc.lineAt !== "function" ||
    typeof doc.line !== "function" ||
    !Number.isInteger(doc.lines)
  ) {
    return null;
  }

  const sourceLineCount = rowCount + 1;
  const nearbyCandidates = new Map();

  for (const position of positions) {
    let anchorLine;
    try {
      anchorLine = doc.lineAt(position).number;
    } catch (error) {
      continue;
    }

    const firstStart = Math.max(1, anchorLine - sourceLineCount);
    const lastStart = Math.min(
      anchorLine + 1,
      doc.lines - sourceLineCount + 1
    );

    for (let startLine = firstStart; startLine <= lastStart; startLine++) {
      const endLine = startLine + sourceLineCount - 1;
      if (endLine > doc.lines) continue;

      const firstLine = doc.line(startLine);
      const lastLine = doc.line(endLine);
      if (position < firstLine.from - 1 || position > lastLine.to + 1) continue;

      const parsed = parseTableCandidate(
        doc.sliceString(firstLine.from, lastLine.to),
        rowCount,
        columnCount
      );
      if (parsed) {
        nearbyCandidates.set(
          firstLine.from + ":" + lastLine.to,
          parsed
        );
      }
    }
  }

  return nearbyCandidates.size === 1
    ? nearbyCandidates.values().next().value
    : null;
}

function findWidgetDocumentPositions(view, widget, docLength) {
  const positions = new Set();
  const offsets = [0];
  if (widget.childNodes) offsets.push(widget.childNodes.length);

  for (const offset of offsets) {
    try {
      const position = view.posAtDOM(widget, offset);
      if (Number.isInteger(position)) {
        positions.add(Math.max(0, Math.min(docLength, position)));
      }
    } catch (error) {
      // Some CodeMirror widgets expose only one of their DOM boundaries.
    }
  }

  return Array.from(positions);
}

function parseTableCandidate(source, rowCount, columnCount) {
  const parsed = parseMarkdownTableSource(source);
  if (
    !parsed ||
    parsed.rows.length !== rowCount ||
    parsed.rows.some((row) => row.length !== columnCount)
  ) {
    return null;
  }
  return parsed;
}

function parseMarkdownTableSource(source) {
  const lines = source.split(/\r\n|\r|\n/);
  while (lines.length > 0 && /^\s*$/.test(lines[0])) lines.shift();
  while (lines.length > 0 && /^\s*$/.test(lines[lines.length - 1])) lines.pop();
  if (lines.length < 2) return null;

  const sourceRows = lines.map(splitMarkdownTableRow);
  if (sourceRows.some((row) => row === null)) return null;

  const columnCount = sourceRows[0].length;
  if (
    columnCount === 0 ||
    sourceRows.some((row) => row.length !== columnCount) ||
    !isMarkdownTableDelimiterRow(sourceRows[1])
  ) {
    return null;
  }

  return {
    rows: [sourceRows[0], ...sourceRows.slice(2)]
  };
}

function splitMarkdownTableRow(line) {
  const source = line.trim();
  if (!source) return null;

  const separators = [];
  for (let position = 0; position < source.length; position++) {
    if (source.charCodeAt(position) === 96) {
      const codeEnd = findInlineCodeEnd(source, position);
      if (codeEnd > position) {
        position = codeEnd - 1;
        continue;
      }
    }

    if (source[position] === "|" && !isEscapedCharacter(source, position)) {
      separators.push(position);
    }
  }
  if (separators.length === 0) return null;

  const cells = [];
  let cellStart = 0;
  for (const separator of separators) {
    cells.push(source.slice(cellStart, separator));
    cellStart = separator + 1;
  }
  cells.push(source.slice(cellStart));

  if (separators[0] === 0) cells.shift();
  if (separators[separators.length - 1] === source.length - 1) cells.pop();

  return cells.map((cell) => cell.trim());
}

function isMarkdownTableDelimiterRow(cells) {
  return cells.length > 0 && cells.every((cell) => /^:?-+:?$/.test(cell));
}

function isEscapedCharacter(source, index) {
  let slashCount = 0;
  for (let position = index - 1; position >= 0 && source[position] === "\\"; position--) {
    slashCount++;
  }
  return slashCount % 2 === 1;
}

function commonmarkVisibleText(source) {
  let visible = "";

  for (let position = 0; position < source.length; position++) {
    if (
      source[position] === "\\" &&
      position + 1 < source.length &&
      COMMONMARK_ESCAPABLE.has(source[position + 1])
    ) {
      visible += source[position + 1];
      position++;
    } else {
      visible += source[position];
    }
  }

  return visible;
}

function replaceProjectedMath(root, mathRanges) {
  const projection = buildTextProjection(root);
  const matches = findProjectedMathMatches(projection.text, mathRanges);
  if (!matches || matches.length === 0) return false;

  const doc = root.ownerDocument || document;
  const replacements = [];

  for (const match of matches) {
    const start = findProjectionBoundary(projection.segments, match.from, false);
    const end = findProjectionBoundary(projection.segments, match.to, true);
    if (!start || !end) return false;

    let rendered;
    try {
      rendered = renderMath(match.math.source.trim(), match.math.display);
    } catch (error) {
      return false;
    }
    if (!rendered) return false;

    replacements.push({ start, end, rendered });
  }

  for (let index = replacements.length - 1; index >= 0; index--) {
    const replacement = replacements[index];
    const range = doc.createRange();
    range.setStart(replacement.start.node, replacement.start.offset);
    range.setEnd(replacement.end.node, replacement.end.offset);
    range.deleteContents();
    range.insertNode(replacement.rendered);
  }

  return true;
}

function buildTextProjection(root) {
  const doc = root.ownerDocument || document;
  const walker = doc.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const segments = [];
  let text = "";
  let previousWasSkipped = false;

  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    if (!node.nodeValue || !node.parentElement) continue;

    if (isInsideSkippedRegion(node, root)) {
      if (!previousWasSkipped) text += PROJECTION_GAP;
      previousWasSkipped = true;
      continue;
    }

    previousWasSkipped = false;
    const from = text.length;
    text += node.nodeValue;
    segments.push({ node, from, to: text.length });
  }

  return { text, segments };
}

function findProjectedMathMatches(text, mathRanges) {
  const expected = mathRanges.map((math) => ({
    math,
    visible: commonmarkVisibleText(math.raw)
  }));
  if (
    expected.some(
      (item) => !item.visible || item.visible.includes(PROJECTION_GAP)
    )
  ) {
    return null;
  }

  const expectedCounts = new Map();
  for (const item of expected) {
    expectedCounts.set(
      item.visible,
      (expectedCounts.get(item.visible) || 0) + 1
    );
  }

  for (const [visible, count] of expectedCounts) {
    if (countNonOverlappingOccurrences(text, visible) !== count) {
      return null;
    }
  }

  const matches = [];
  let searchFrom = 0;
  for (const item of expected) {
    const from = text.indexOf(item.visible, searchFrom);
    if (from < 0) return null;
    const to = from + item.visible.length;
    matches.push({ math: item.math, from, to });
    searchFrom = to;
  }

  return matches;
}

function countNonOverlappingOccurrences(text, search) {
  let count = 0;
  let position = 0;

  while (position <= text.length - search.length) {
    const found = text.indexOf(search, position);
    if (found < 0) break;
    count++;
    position = found + search.length;
  }

  return count;
}

function findProjectionBoundary(segments, offset, endBoundary) {
  for (const segment of segments) {
    const containsOffset = endBoundary
      ? offset > segment.from && offset <= segment.to
      : offset >= segment.from && offset < segment.to;
    if (containsOffset) {
      return {
        node: segment.node,
        offset: offset - segment.from
      };
    }
  }
  return null;
}

async function renderSectionFromSource(plugin, el, ctx) {
  const section = ctx.getSectionInfo(el);
  const sectionSource = extractSectionSource(section);
  if (!sectionSource || !hasLegacyMathDelimiter(sectionSource)) return false;

  const transformed = transformLegacyMathDelimiters(sectionSource);
  if (transformed === sectionSource) return false;

  el.dataset.latexDelimiterCompat = "rendered";

  const doc = el.ownerDocument || document;
  const temp = doc.createElement("div");
  await MarkdownRenderer.render(plugin.app, transformed, temp, ctx.sourcePath, plugin);

  const children = Array.from(temp.childNodes);
  if (
    children.length === 1 &&
    children[0].nodeType === Node.ELEMENT_NODE &&
    children[0].tagName === el.tagName
  ) {
    el.replaceChildren(...Array.from(children[0].childNodes));
  } else {
    el.replaceChildren(...children);
  }

  return true;
}

function extractSectionSource(section) {
  if (
    !section ||
    typeof section.text !== "string" ||
    !Number.isInteger(section.lineStart) ||
    !Number.isInteger(section.lineEnd) ||
    section.lineStart < 0 ||
    section.lineEnd < section.lineStart
  ) {
    return null;
  }

  const lines = section.text.split(/\r?\n/);
  if (section.lineEnd >= lines.length) return null;
  return lines.slice(section.lineStart, section.lineEnd + 1).join("\n");
}

function hasLegacyMathDelimiter(source) {
  return source.includes("\\(") || source.includes("\\[");
}

function transformLegacyMathDelimiters(source) {
  const ranges = findLegacyMathRanges(source);
  if (ranges.length === 0) return source;

  let out = "";
  let pos = 0;

  for (const range of ranges) {
    out += source.slice(pos, range.from);
    out += range.display ? makeDisplayMath(range.source) : `$${range.source}$`;
    pos = range.to;
  }

  return out + source.slice(pos);
}

function findLegacyMathRanges(source) {
  const literalRanges = findLiteralRanges(source);
  const ranges = [];
  let literalIndex = 0;
  let pos = 0;

  while (pos < source.length) {
    while (literalIndex < literalRanges.length && pos >= literalRanges[literalIndex].end) {
      literalIndex++;
    }

    const literal = literalRanges[literalIndex];
    if (literal && pos >= literal.start && pos < literal.end) {
      pos = literal.end;
      continue;
    }

    if (
      source[pos] !== "\\" ||
      isEscapedDelimiterSlash(source, pos) ||
      (source[pos + 1] !== "(" && source[pos + 1] !== "[")
    ) {
      pos++;
      continue;
    }

    const display = source[pos + 1] === "[";
    const close = findSourceClosing(source, pos + 2, display);
    if (close < 0) {
      pos++;
      continue;
    }

    const to = close + 2;
    const mathSource = source.slice(pos + 2, close);
    const normalizedInline = display ? null : normalizeInlineMathSource(mathSource);
    const valid =
      mathSource.trim().length > 0 &&
      (display || normalizedInline !== null) &&
      !rangeOverlapsLiteralRange(pos, to, literalRanges, literalIndex);

    if (!valid) {
      pos++;
      continue;
    }

    ranges.push({
      from: pos,
      to,
      source: display ? mathSource : normalizedInline.source,
      display,
      multilineInline: !display && normalizedInline.multiline,
      raw: source.slice(pos, to)
    });
    pos = to;
  }

  return ranges;
}

function normalizeInlineMathSource(source) {
  const trimmed = source.trim();
  if (!trimmed) return null;

  const lineBreakPattern = /\r\n|\r|\n/g;
  const lineBreaks = [];
  let match;

  while ((match = lineBreakPattern.exec(source)) !== null) {
    lineBreaks.push({ index: match.index, length: match[0].length });
  }

  if (lineBreaks.length === 0) {
    return { source: trimmed, multiline: false };
  }
  if (lineBreaks.length !== 1) return null;

  const lineBreak = lineBreaks[0];
  const before = source.slice(0, lineBreak.index);
  const after = source.slice(lineBreak.index + lineBreak.length);

  if (!before.trim() || !after.trim()) return null;
  if (/[ \t]{2,}$/.test(before) || /\\$/.test(before)) return null;
  if (crossesMarkdownTableBoundary(before, after)) return null;
  if (startsMarkdownBlockAfterSoftBreak(after)) return null;

  return {
    source: (before.trimEnd() + " " + after.trimStart()).trim(),
    multiline: true
  };
}

function crossesMarkdownTableBoundary(before, after) {
  const tableSeparator = /(?:^|[ \t])\|(?:[ \t]|$)/;
  return /^[ \t]*\|/.test(after) ||
    (tableSeparator.test(before) && tableSeparator.test(after));
}

function startsMarkdownBlockAfterSoftBreak(source) {
  const blockStartPatterns = [
    /^(?: {4}|\t)/,
    /^ {0,3}(?:#{1,6}(?:[ \t]|$)|>|(?:[-+*]|\d+[.)])[ \t]+)/,
    /^ {0,3}(?:\x60{3,}|~{3,})/,
    /^ {0,3}(?:[-*_][ \t]*){3,}(?:$|\r|\n)/,
    /^ {0,3}(?:=+|-+)[ \t]*(?:$|\r|\n)/,
    /^ {0,3}\[[^\]\r\n]+\]:[ \t]*(?:\S|$)/,
    /^ {0,3}(?:<!--|<\?|<!\[CDATA\[|<![A-Z]|<\/?[A-Za-z][A-Za-z0-9-]*(?:[ \t/>]|$))/
  ];
  return blockStartPatterns.some((pattern) => pattern.test(source));
}

function findLiteralRanges(source) {
  const ranges = findFenceRanges(source);
  const frontmatter = findFrontmatterRange(source);
  if (frontmatter) ranges.push(frontmatter);

  ranges.sort((a, b) => a.start - b.start);

  let rangeIndex = 0;
  let pos = 0;
  while (pos < source.length) {
    while (rangeIndex < ranges.length && pos >= ranges[rangeIndex].end) {
      rangeIndex++;
    }

    const range = ranges[rangeIndex];
    if (range && pos >= range.start && pos < range.end) {
      pos = range.end;
      continue;
    }

    if (source[pos] === "`") {
      const codeEnd = findInlineCodeEnd(source, pos);
      if (codeEnd > pos) {
        ranges.push({ start: pos, end: codeEnd });
        pos = codeEnd;
        continue;
      }
    }

    pos++;
  }

  return mergeRanges(ranges);
}

function findFrontmatterRange(source) {
  const linePattern = /[^\r\n]*(?:\r\n|\r|\n|$)/g;
  let match;
  let firstLine = true;

  while ((match = linePattern.exec(source)) && match[0] !== "") {
    const line = match[0].replace(/(?:\r\n|\r|\n)$/, "");
    const trimmed = firstLine ? line.replace(/^\uFEFF/, "").trim() : line.trim();

    if (firstLine) {
      firstLine = false;
      if (trimmed !== "---") return null;
    } else if (trimmed === "---" || trimmed === "...") {
      return { start: 0, end: match.index + match[0].length };
    }

    if (linePattern.lastIndex >= source.length) break;
  }

  return null;
}

function rangeOverlapsLiteralRange(from, to, ranges, startIndex) {
  for (let i = startIndex; i < ranges.length && ranges[i].start < to; i++) {
    if (ranges[i].end > from) return true;
  }
  return false;
}

function mergeRanges(ranges) {
  const sorted = ranges.slice().sort((a, b) => a.start - b.start || a.end - b.end);
  const merged = [];

  for (const range of sorted) {
    const previous = merged[merged.length - 1];
    if (previous && range.start <= previous.end) {
      previous.end = Math.max(previous.end, range.end);
    } else {
      merged.push({ start: range.start, end: range.end });
    }
  }

  return merged;
}

function findFenceRanges(source) {
  const ranges = [];
  const linePattern = /[^\r\n]*(?:\r\n|\r|\n|$)/g;
  let match;
  let inFence = false;
  let fenceStart = -1;
  let fenceMarker = "";
  let fenceLength = 0;

  while ((match = linePattern.exec(source)) && match[0] !== "") {
    const line = match[0];
    const trimmed = line.trimStart();
    const fenceMatch = trimmed.match(/^(```+|~~~+)/);

    if (!inFence && fenceMatch) {
      inFence = true;
      fenceStart = match.index;
      fenceMarker = fenceMatch[1][0];
      fenceLength = fenceMatch[1].length;
    } else if (inFence && isFenceClosingLine(trimmed, fenceMarker, fenceLength)) {
      ranges.push({ start: fenceStart, end: match.index + line.length });
      inFence = false;
      fenceStart = -1;
      fenceMarker = "";
      fenceLength = 0;
    }

    if (linePattern.lastIndex >= source.length) break;
  }

  if (inFence) {
    ranges.push({ start: fenceStart, end: source.length });
  }

  return ranges;
}

function isFenceClosingLine(line, marker, minimumLength) {
  if (!marker || line[0] !== marker) return false;

  let markerCount = 0;
  while (line[markerCount] === marker) markerCount++;
  if (markerCount < minimumLength) return false;

  return /^[ \t]*(?:\r?\n|\r)?$/.test(line.slice(markerCount));
}

function findInlineCodeEnd(source, start) {
  let tickCount = 0;
  while (source[start + tickCount] === "`") tickCount++;
  const ticks = "`".repeat(tickCount);
  let searchFrom = start + tickCount;

  while (searchFrom < source.length) {
    const close = source.indexOf(ticks, searchFrom);
    if (close < 0) return -1;

    const exactRun = source[close - 1] !== "`" && source[close + tickCount] !== "`";
    if (exactRun) return close + tickCount;
    searchFrom = close + tickCount;
  }

  return -1;
}

function findSourceClosing(source, from, display) {
  const closeChar = display ? "]" : ")";

  for (let i = from; i < source.length - 1; i++) {
    if (
      source[i] === "\\" &&
      source[i + 1] === closeChar &&
      !isEscapedDelimiterSlash(source, i)
    ) {
      return i;
    }
  }

  return -1;
}

function makeDisplayMath(source) {
  const body = source.trim();
  if (!body) return "\n\n$$ $$\n\n";
  return `\n\n$$\n${body}\n$$\n\n`;
}

function renderLegacyMathDelimiters(root) {
  const textNodes = collectTextNodes(root);
  let changed = false;

  for (const node of textNodes) {
    if (replaceLegacyMathInTextNode(node)) {
      changed = true;
    }
  }

  return changed;
}

function collectTextNodes(root) {
  const nodes = [];
  const doc = root.ownerDocument || document;
  const walker = doc.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue || !node.nodeValue.includes("\\") || !node.parentElement) {
        return NodeFilter.FILTER_REJECT;
      }
      if (isInsideSkippedRegion(node, root)) {
        return NodeFilter.FILTER_REJECT;
      }
      return NodeFilter.FILTER_ACCEPT;
    }
  });

  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    nodes.push(node);
  }

  return nodes;
}

function isInsideSkippedRegion(node, root) {
  const skippedAncestor = node.parentElement?.closest(SKIP_SELECTOR);
  return Boolean(
    skippedAncestor &&
    (skippedAncestor === root || root.contains(skippedAncestor))
  );
}

function replaceLegacyMathInTextNode(node) {
  const text = node.nodeValue;
  const parts = parseLegacyMath(text);
  if (!parts) return false;

  const frag = (node.ownerDocument || document).createDocumentFragment();

  for (const part of parts) {
    if (part.type === "text") {
      frag.appendChild((node.ownerDocument || document).createTextNode(part.value));
      continue;
    }

    try {
      frag.appendChild(renderMath(part.value.trim(), part.display));
    } catch (error) {
      frag.appendChild((node.ownerDocument || document).createTextNode(part.raw));
    }
  }

  node.parentNode.replaceChild(frag, node);
  return true;
}

function parseLegacyMath(text) {
  const parts = [];
  let scanPos = 0;
  let emitPos = 0;
  let changed = false;

  while (scanPos < text.length) {
    const open = findNextOpening(text, scanPos);
    if (!open) break;

    const close = findClosing(text, open.end, open.display);
    if (!close) break;

    const source = text.slice(open.end, close.start);
    const normalized = open.display
      ? source.trim()
        ? { source }
        : null
      : normalizeInlineMathSource(source);

    if (!normalized) {
      scanPos = close.end;
      continue;
    }

    if (open.start > emitPos) {
      parts.push({ type: "text", value: text.slice(emitPos, open.start) });
    }

    parts.push({
      type: "math",
      value: normalized.source,
      display: open.display,
      raw: text.slice(open.start, close.end)
    });

    changed = true;
    scanPos = close.end;
    emitPos = close.end;
  }

  if (!changed) return null;
  if (emitPos < text.length) {
    parts.push({ type: "text", value: text.slice(emitPos) });
  }

  return parts;
}

function findNextOpening(text, from) {
  let best = null;

  for (let i = from; i < text.length - 1; i++) {
    if (text[i] !== "\\" || isEscapedDelimiterSlash(text, i)) continue;

    const next = text[i + 1];
    if (next !== "(" && next !== "[") continue;

    const found = {
      start: i,
      end: i + 2,
      display: next === "["
    };

    if (!best || found.start < best.start) {
      best = found;
    }
  }

  return best;
}

function findClosing(text, from, display) {
  const closeChar = display ? "]" : ")";

  for (let i = from; i < text.length - 1; i++) {
    if (text[i] === "\\" && text[i + 1] === closeChar && !isEscapedDelimiterSlash(text, i)) {
      return { start: i, end: i + 2 };
    }
  }

  return null;
}

function isEscapedDelimiterSlash(text, index) {
  let slashCount = 0;
  for (let i = index - 1; i >= 0 && text[i] === "\\"; i--) {
    slashCount++;
  }
  return slashCount % 2 === 1;
}
