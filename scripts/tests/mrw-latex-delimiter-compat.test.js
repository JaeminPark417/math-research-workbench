const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const livePreviewField = {};

class MockPlugin {}
class MockWidgetType {}

class MockRangeSetBuilder {
  constructor() {
    this.items = [];
  }

  add(from, to, value) {
    this.items.push({ from, to, value });
  }

  finish() {
    return this.items;
  }
}

const MockDecoration = {
  none: [],
  replace(spec) {
    return spec;
  }
};

const renderMathCalls = [];
const editorViewFindCalls = [];
const mockFoundEditorView = { id: "outer-editor-view" };
const moduleRecord = { exports: {} };
const sandbox = {
  module: moduleRecord,
  exports: moduleRecord.exports,
  queueMicrotask,
  setTimeout,
  clearTimeout,
  NodeFilter: {
    SHOW_TEXT: 4,
    FILTER_REJECT: 2,
    FILTER_ACCEPT: 1
  },
  require(id) {
    if (id === "obsidian") {
      return {
        Plugin: MockPlugin,
        MarkdownRenderer: {},
        renderMath(source, displayMode) {
          const rendered = { source, displayMode };
          renderMathCalls.push(rendered);
          return rendered;
        },
        finishRenderMath() {},
        editorLivePreviewField: livePreviewField
      };
    }
    if (id === "@codemirror/state") {
      return {
        StateField: {
          define(spec) {
            return spec;
          }
        },
        RangeSetBuilder: MockRangeSetBuilder
      };
    }
    if (id === "@codemirror/view") {
      return {
        Decoration: MockDecoration,
        EditorView: {
          findFromDOM(element) {
            editorViewFindCalls.push(element);
            return mockFoundEditorView;
          },
          decorations: {
            from() {
              return null;
            }
          },
          baseTheme(theme) {
            return theme;
          }
        },
        ViewPlugin: {
          fromClass() {
            return {};
          }
        },
        WidgetType: MockWidgetType
      };
    }
    throw new Error("Unexpected module: " + id);
  }
};

const pluginPath = path.join(
  __dirname,
  "..",
  "..",
  "optional",
  "obsidian-plugins",
  "mrw-latex-delimiter-compat",
  "main.js"
);
const pluginSource = fs.readFileSync(pluginPath, "utf8");
const exposedNames = [
  "findLegacyMathRanges",
  "transformLegacyMathDelimiters",
  "parseLegacyMath",
  "normalizeInlineMathSource",
  "buildStructuralMathDecorations",
  "buildInlineMathDecorations",
  "isInsideSkippedRegion",
  "splitMarkdownTableRow",
  "parseMarkdownTableSource",
  "commonmarkVisibleText",
  "findProjectedMathMatches",
  "findRawTableCellSource",
  "findTableDataForWidget",
  "replaceProjectedMath",
  "findOuterEditorView",
  "initializeTableCellRetries",
  "renderTableCellFromEditorSource",
  "extractSectionSource"
];
vm.runInNewContext(
  pluginSource + "\nmodule.exports.__test = { " + exposedNames.join(", ") + " };",
  sandbox,
  { filename: pluginPath }
);

const {
  findLegacyMathRanges,
  transformLegacyMathDelimiters,
  parseLegacyMath,
  normalizeInlineMathSource,
  buildStructuralMathDecorations,
  buildInlineMathDecorations,
  isInsideSkippedRegion,
  splitMarkdownTableRow,
  parseMarkdownTableSource,
  commonmarkVisibleText,
  findProjectedMathMatches,
  findRawTableCellSource,
  findTableDataForWidget,
  replaceProjectedMath,
  findOuterEditorView,
  initializeTableCellRetries,
  renderTableCellFromEditorSource,
  extractSectionSource
} = moduleRecord.exports.__test;

const inline = (body) => "\\(" + body + "\\)";
const display = (body) => "\\[" + body + "\\]";
const plain = (value) => JSON.parse(JSON.stringify(value));
const tick = String.fromCharCode(96);

const fullSectionText = "first " + inline("x") + "\n\nsecond\n\nthird";
assert.equal(
  extractSectionSource({ text: fullSectionText, lineStart: 0, lineEnd: 0 }),
  "first " + inline("x")
);
assert.equal(
  extractSectionSource({ text: fullSectionText, lineStart: 2, lineEnd: 2 }),
  "second"
);
assert.equal(
  extractSectionSource({ text: "a\r\nb", lineStart: 1, lineEnd: 1 }),
  "b"
);
assert.equal(
  extractSectionSource({ text: fullSectionText, lineStart: 4, lineEnd: 5 }),
  null
);

const outerEditor = { className: "cm-editor" };
const nestedCode = { tagName: "CODE" };
const nestedCellEditor = { className: "cm-editor" };
const postProcessorRoot = {
  contains(element) {
    return element === nestedCode || element === nestedCellEditor;
  }
};
const textNodeUnder = (skippedAncestor) => ({
  parentElement: {
    closest() {
      return skippedAncestor;
    }
  }
});

assert.equal(isInsideSkippedRegion(textNodeUnder(outerEditor), postProcessorRoot), false);
assert.equal(isInsideSkippedRegion(textNodeUnder(nestedCode), postProcessorRoot), true);
assert.equal(isInsideSkippedRegion(textNodeUnder(nestedCellEditor), postProcessorRoot), true);
assert.equal(isInsideSkippedRegion(textNodeUnder(postProcessorRoot), postProcessorRoot), true);
assert.equal(isInsideSkippedRegion(textNodeUnder(null), postProcessorRoot), false);

const tableOuterEditor = { className: "cm-editor" };
const tableWidgetWithNestedEditor = {
  closest(selector) {
    assert.equal(selector, ".cm-editor");
    return tableOuterEditor;
  },
  querySelector() {
    throw new Error("The table widget must not be searched for a nested editor.");
  }
};
assert.equal(findOuterEditorView(tableWidgetWithNestedEditor), mockFoundEditorView);
assert.equal(editorViewFindCalls.at(-1), tableOuterEditor);

const retryCallbacks = new Map();
const cancelledRetryFrames = [];
let nextRetryFrameId = 1;
const retryWindow = {
  requestAnimationFrame(callback) {
    const id = nextRetryFrameId++;
    retryCallbacks.set(id, callback);
    return id;
  },
  cancelAnimationFrame(id) {
    cancelledRetryFrames.push(id);
    retryCallbacks.delete(id);
  }
};
let retryCleanup;
const retryPlugin = {
  register(cleanup) {
    retryCleanup = cleanup;
  }
};
initializeTableCellRetries(retryPlugin);

let retryTableIsAttached = false;
const retryRow = { cells: [] };
const retryTable = { rows: [retryRow] };
const retryCell = {
  parentElement: retryRow,
  closest(selector) {
    assert.equal(selector, "table");
    return retryTable;
  }
};
retryRow.cells.push(retryCell);
const retryWidget = {
  childNodes: [{}],
  matches(selector) {
    assert.equal(selector, ".cm-table-widget");
    return true;
  },
  contains(element) {
    if (element === retryTable) return retryTableIsAttached;
    return (
      retryTableIsAttached &&
      element?.closest?.("th,td") === retryCell
    );
  },
  closest(selector) {
    assert.equal(selector, ".cm-editor");
    return tableOuterEditor;
  }
};
const makeRetryRoot = (isConnected = true) => ({
  ownerDocument: { defaultView: retryWindow },
  isConnected,
  closest(selector) {
    assert.equal(selector, "th,td");
    return retryCell;
  }
});
const retryRoot = makeRetryRoot(false);
const retryContext = { containerEl: retryWidget };

assert.equal(
  renderTableCellFromEditorSource(retryPlugin, retryRoot, retryContext),
  true
);
assert.equal(retryPlugin.pendingTableCells.has(retryRoot), true);
assert.equal(retryPlugin.tableCellRetryHandles.size, 1);
assert.equal(retryCallbacks.size, 1);

assert.equal(
  renderTableCellFromEditorSource(retryPlugin, retryRoot, retryContext),
  true
);
assert.equal(retryCallbacks.size, 1);

const editorViewFindCountBeforeDetachedRetry = editorViewFindCalls.length;
retryTableIsAttached = true;
retryCallbacks.get(1)();
assert.equal(
  editorViewFindCalls.length,
  editorViewFindCountBeforeDetachedRetry + 1
);
assert.equal(retryPlugin.pendingTableCells.has(retryRoot), false);
assert.equal(retryPlugin.tableCellRetryHandles.size, 0);
assert.equal(retryCallbacks.size, 1);

retryTableIsAttached = false;
const retryRootCancelledOnUnload = makeRetryRoot();
assert.equal(
  renderTableCellFromEditorSource(
    retryPlugin,
    retryRootCancelledOnUnload,
    retryContext
  ),
  true
);
assert.equal(retryCallbacks.size, 2);
retryCleanup();
assert.equal(retryPlugin.tableCellRetriesActive, false);
assert.deepEqual(cancelledRetryFrames, [2]);
assert.equal(retryCallbacks.has(2), false);

assert.deepEqual(plain(splitMarkdownTableRow("| A | B |")), ["A", "B"]);
assert.deepEqual(plain(splitMarkdownTableRow("A | B")), ["A", "B"]);
assert.deepEqual(
  plain(splitMarkdownTableRow("| a\\|b | " + tick + "c|d" + tick + " |")),
  ["a\\|b", tick + "c|d" + tick]
);
assert.equal(splitMarkdownTableRow("no table delimiter"), null);

const parsedTable = plain(
  parseMarkdownTableSource(
    "| Name | Formula |\n" +
      "| :--- | ---: |\n" +
      "| first | " +
      inline("\\{x\\}") +
      " |"
  )
);
assert.deepEqual(parsedTable, {
  rows: [
    ["Name", "Formula"],
    ["first", inline("\\{x\\}")]
  ]
});
assert.deepEqual(
  plain(parseMarkdownTableSource("A | B\n--- | ---\nx | y")),
  {
    rows: [
      ["A", "B"],
      ["x", "y"]
    ]
  }
);
assert.equal(
  parseMarkdownTableSource("| A | B |\n| --- | --- |\n| only one |"),
  null
);

assert.equal(commonmarkVisibleText(inline("\\{x\\}")), "({x})");
assert.equal(commonmarkVisibleText(inline("\\|x\\|")), "(|x|)");
assert.equal(
  commonmarkVisibleText(inline("\\dim_H K")),
  "(" + "\\dim_H K" + ")"
);

let projectedRanges = findLegacyMathRanges(
  "value " + inline("\\{x\\}") + " end"
);
let projectedMatches = plain(
  findProjectedMathMatches("value ({x}) end", projectedRanges)
);
assert.equal(projectedMatches.length, 1);
assert.equal(projectedMatches[0].from, 6);
assert.equal(projectedMatches[0].to, 11);
assert.equal(projectedMatches[0].math.source, "\\{x\\}");

assert.equal(
  findProjectedMathMatches("value (x), repeated (x)", findLegacyMathRanges(inline("x"))),
  null
);

projectedRanges = findLegacyMathRanges(inline("x") + " and " + inline("x"));
projectedMatches = plain(
  findProjectedMathMatches("(x) and (x)", projectedRanges)
);
assert.deepEqual(
  projectedMatches.map(({ from, to }) => ({ from, to })),
  [
    { from: 0, to: 3 },
    { from: 8, to: 11 }
  ]
);

const firstFormulaText = {
  nodeValue: "prefix (",
  parentElement: textNodeUnder(outerEditor).parentElement
};
const secondFormulaText = {
  nodeValue: "x) suffix",
  parentElement: textNodeUnder(outerEditor).parentElement
};
const domRangeCalls = [];
const projectionDocument = {
  createTreeWalker() {
    const nodes = [firstFormulaText, secondFormulaText];
    let index = 0;
    return {
      nextNode() {
        return nodes[index++] || null;
      }
    };
  },
  createRange() {
    const call = {};
    domRangeCalls.push(call);
    return {
      setStart(node, offset) {
        call.start = { node, offset };
      },
      setEnd(node, offset) {
        call.end = { node, offset };
      },
      deleteContents() {
        call.deleted = true;
      },
      insertNode(node) {
        call.inserted = node;
      }
    };
  }
};
const projectionRoot = {
  ownerDocument: projectionDocument,
  contains() {
    return false;
  }
};
const renderCallCount = renderMathCalls.length;
assert.equal(
  replaceProjectedMath(projectionRoot, findLegacyMathRanges(inline("x"))),
  true
);
assert.equal(renderMathCalls.length, renderCallCount + 1);
assert.deepEqual(plain(renderMathCalls.at(-1)), {
  source: "x",
  displayMode: false
});
assert.equal(domRangeCalls.length, 1);
assert.equal(domRangeCalls[0].start.node, firstFormulaText);
assert.equal(domRangeCalls[0].start.offset, 7);
assert.equal(domRangeCalls[0].end.node, secondFormulaText);
assert.equal(domRangeCalls[0].end.offset, 2);
assert.equal(domRangeCalls[0].deleted, true);
assert.equal(domRangeCalls[0].inserted, renderMathCalls.at(-1));

const directCellText = {
  nodeValue: "prefix (x) suffix",
  parentElement: {
    closest() {
      return null;
    }
  }
};
const directRangeCalls = [];
const directDocument = {
  createTreeWalker() {
    let returned = false;
    return {
      nextNode() {
        if (returned) return null;
        returned = true;
        return directCellText;
      }
    };
  },
  createRange() {
    const call = {};
    directRangeCalls.push(call);
    return {
      setStart(node, offset) {
        call.start = { node, offset };
      },
      setEnd(node, offset) {
        call.end = { node, offset };
      },
      deleteContents() {
        call.deleted = true;
      },
      insertNode(node) {
        call.inserted = node;
      }
    };
  }
};
const directRow = { cells: [] };
const directTable = { rows: [directRow] };
const directCell = {
  parentElement: directRow,
  closest(selector) {
    assert.equal(selector, "table");
    return directTable;
  }
};
directRow.cells.push(directCell);
const directWidget = {
  matches(selector) {
    assert.equal(selector, ".cm-table-widget");
    return true;
  },
  contains(element) {
    return element === directTable;
  },
  closest() {
    throw new Error("The core-backed source path must not find an outer editor.");
  }
};
directWidget.cmView = {
  widget: {
    containerEl: directWidget,
    rows: [[{ text: inline("x") }]]
  }
};
const directRoot = {
  ownerDocument: directDocument,
  closest(selector) {
    assert.equal(selector, "th,td");
    return directCell;
  }
};
const editorViewFindCount = editorViewFindCalls.length;
assert.equal(
  renderTableCellFromEditorSource(
    retryPlugin,
    directRoot,
    { containerEl: directWidget }
  ),
  true
);
assert.equal(editorViewFindCalls.length, editorViewFindCount);
assert.equal(directRangeCalls.length, 1);
assert.equal(directRangeCalls[0].start.offset, 7);
assert.equal(directRangeCalls[0].end.offset, 10);
assert.equal(directRangeCalls[0].deleted, true);
assert.equal(directRangeCalls[0].inserted.source, "x");

function makeTextDocument(text) {
  const starts = [0];
  for (let index = 0; index < text.length; index++) {
    if (text[index] === "\n") starts.push(index + 1);
  }

  const line = (number) => {
    if (number < 1 || number > starts.length) {
      throw new RangeError("line out of range");
    }
    const from = starts[number - 1];
    const nextStart = number < starts.length ? starts[number] : text.length + 1;
    const to = number < starts.length ? nextStart - 1 : text.length;
    return { from, to, number, text: text.slice(from, to) };
  };

  return {
    length: text.length,
    lines: starts.length,
    sliceString(from, to) {
      return text.slice(from, to);
    },
    line,
    lineAt(position) {
      if (position < 0 || position > text.length) {
        throw new RangeError("position out of range");
      }
      let number = 1;
      while (number < starts.length && starts[number] <= position) number++;
      return line(number);
    }
  };
}

const tableDocumentSource =
  "intro\n\n" +
  "| A | B |\n" +
  "| --- | --- |\n" +
  "| " +
  inline("x") +
  " | y |\n\n" +
  "after";
const tableDocument = makeTextDocument(tableDocumentSource);
const tableFrom = tableDocumentSource.indexOf("| A | B |");
const tableTo = tableDocumentSource.indexOf("\n\nafter");
const tableWidget = { childNodes: [{}] };
const tableView = {
  state: { doc: tableDocument },
  posAtDOM(widget, offset) {
    assert.equal(widget, tableWidget);
    return offset === 0 ? tableFrom : tableTo;
  },
  lineBlockAt(position) {
    return tableDocument.lineAt(position);
  }
};
assert.deepEqual(
  plain(findTableDataForWidget(tableView, tableWidget, 2, 2)),
  {
    rows: [
      ["A", "B"],
      [inline("x"), "y"]
    ]
  }
);
assert.equal(findTableDataForWidget(tableView, tableWidget, 3, 2), null);

const coreBackedTableWidget = {};
coreBackedTableWidget.cmView = {
  widget: {
    containerEl: coreBackedTableWidget,
    rows: [
      [{ text: "Header" }, { text: "Formula" }],
      [{ text: "first" }, { text: inline("x") }]
    ]
  }
};
assert.equal(
  findRawTableCellSource(coreBackedTableWidget, 1, 1, 2, 2),
  inline("x")
);
assert.equal(findRawTableCellSource(coreBackedTableWidget, 5, 1, 2, 2), null);
assert.equal(findRawTableCellSource(coreBackedTableWidget, 1, 1, 3, 2), null);
assert.equal(
  findRawTableCellSource(
    { cmView: { widget: { containerEl: {}, rows: [[{ text: "raw" }]] } } },
    0,
    0,
    1,
    1
  ),
  null
);
const raggedCoreTableWidget = {};
raggedCoreTableWidget.cmView = {
  widget: {
    containerEl: raggedCoreTableWidget,
    rows: [[{ text: "A" }, { text: "B" }], [{ text: "only one" }]]
  }
};
assert.equal(findRawTableCellSource(raggedCoreTableWidget, 1, 0, 2, 2), null);
const nonStringCoreCellWidget = {};
nonStringCoreCellWidget.cmView = {
  widget: {
    containerEl: nonStringCoreCellWidget,
    rows: [[{ text: null }]]
  }
};
assert.equal(
  findRawTableCellSource(nonStringCoreCellWidget, 0, 0, 1, 1),
  null
);

assert.deepEqual(plain(normalizeInlineMathSource("a+b")), {
  source: "a+b",
  multiline: false
});
assert.deepEqual(plain(normalizeInlineMathSource("a+\nb")), {
  source: "a+ b",
  multiline: true
});
assert.deepEqual(plain(normalizeInlineMathSource("a+\r\nb")), {
  source: "a+ b",
  multiline: true
});
assert.deepEqual(plain(normalizeInlineMathSource("a+\rb")), {
  source: "a+ b",
  multiline: true
});
assert.deepEqual(plain(normalizeInlineMathSource("|x|\n<1")), {
  source: "|x| <1",
  multiline: true
});

for (const rejected of [
  "a\n\nb",
  "a\nb\nc",
  "a  \nb",
  "a\\" + "\n" + "b",
  "a\\\\" + "\n" + "b",
  "a\n# heading",
  "a\n- item",
  "a\n1. item",
  "a\n> quote",
  "a\n" + tick.repeat(3),
  "a\n---",
  "a\n===",
  "a\n    code",
  "a\n| cell |",
  "left | cell\nright | cell",
  "a\n<div>b",
  "a\n[ref]: /x"
]) {
  assert.equal(normalizeInlineMathSource(rejected), null, rejected);
}

let source = "Before " + inline("a+\nb") + " after";
let ranges = plain(findLegacyMathRanges(source));
assert.equal(ranges.length, 1);
assert.equal(ranges[0].source, "a+ b");
assert.equal(ranges[0].multilineInline, true);
assert.equal(ranges[0].raw, inline("a+\nb"));
assert.equal(transformLegacyMathDelimiters(source), "Before $a+ b$ after");

ranges = plain(findLegacyMathRanges(display("a\nb")));
assert.equal(ranges.length, 1);
assert.equal(ranges[0].display, true);
assert.equal(ranges[0].multilineInline, false);
assert.equal(ranges[0].source, "a\nb");

for (const rejected of [
  inline("a\n\nb"),
  inline("a\nb\nc"),
  inline("a  \nb"),
  inline("a\\" + "\n" + "b"),
  inline("a\\\\" + "\n" + "b"),
  inline("a\n- item"),
  inline("a\n| cell |"),
  inline("left | cell\nright | cell"),
  inline("a\n<div>b"),
  inline("a\n[ref]: /x")
]) {
  assert.equal(findLegacyMathRanges(rejected).length, 0, rejected);
  assert.equal(transformLegacyMathDelimiters(rejected), rejected);
}

const escaped = "\\\\" + inline("x").slice(1);
assert.equal(findLegacyMathRanges(escaped).length, 0);
assert.equal(findLegacyMathRanges(tick + inline("hidden") + tick).length, 0);
assert.equal(findLegacyMathRanges("---\nkey: " + inline("hidden") + "\n---\n").length, 0);
assert.equal(findLegacyMathRanges("---\rkey: " + inline("hidden") + "\r---\r").length, 0);
assert.equal(findLegacyMathRanges("\\(a " + tick + "hidden\\)" + tick).length, 0);
assert.equal(
  findLegacyMathRanges("\\(a\n" + tick.repeat(3) + "\nhidden\\)\n" + tick.repeat(3)).length,
  0
);

const fenced =
  tick.repeat(3) +
  "\n" +
  inline("hidden") +
  "\n" +
  tick.repeat(3) +
  "\n" +
  inline("shown");
ranges = plain(findLegacyMathRanges(fenced));
assert.equal(ranges.length, 1);
assert.equal(ranges[0].source, "shown");

const crFenced =
  tick.repeat(3) +
  "\r" +
  inline("hidden") +
  "\r" +
  tick.repeat(3) +
  "\r" +
  inline("shown");
ranges = plain(findLegacyMathRanges(crFenced));
assert.equal(ranges.length, 1);
assert.equal(ranges[0].source, "shown");

const invalid = inline("a\n\nb");
const valid = inline("c");
const parts = plain(parseLegacyMath(invalid + " keep " + valid + " tail"));
assert.equal(parts[0].type, "text");
assert.equal(parts[0].value, invalid + " keep ");
assert.equal(parts[1].type, "math");
assert.equal(parts[1].value, "c");
assert.equal(parts[2].value, " tail");
assert.equal(parseLegacyMath(invalid), null);
assert.equal(parseLegacyMath("\\(unclosed"), null);

const mixedParts = plain(
  parseLegacyMath(valid + " first " + invalid + " middle " + inline("d") + " tail")
);
assert.equal(mixedParts[0].type, "math");
assert.equal(mixedParts[0].value, "c");
assert.equal(mixedParts[1].value, " first " + invalid + " middle ");
assert.equal(mixedParts[2].type, "math");
assert.equal(mixedParts[2].value, "d");
assert.equal(mixedParts[3].value, " tail");

const invalidTailParts = plain(parseLegacyMath(valid + " then " + invalid));
assert.equal(invalidTailParts[0].type, "math");
assert.equal(invalidTailParts[1].value, " then " + invalid);

const mathRangesField = {};
const structuralRanges = [
  {
    from: 10,
    to: 18,
    source: "a b",
    display: false,
    multilineInline: true,
    raw: inline("a\nb")
  }
];
const makeState = (selectionRanges) => ({
  selection: { ranges: selectionRanges },
  field(field) {
    if (field === livePreviewField) return true;
    if (field === mathRangesField) return structuralRanges;
    return false;
  }
});

let decorations = buildStructuralMathDecorations(
  makeState([{ from: 0, to: 0 }]),
  mathRangesField
);
assert.equal(decorations.length, 1);
assert.equal(decorations[0].from, 10);
assert.equal(decorations[0].to, 18);
assert.equal(decorations[0].value.block, false);
assert.equal(decorations[0].value.widget.display, false);

decorations = buildStructuralMathDecorations(
  makeState([{ from: 12, to: 12 }]),
  mathRangesField
);
assert.equal(decorations.length, 0);

const inlineRanges = [
  {
    from: 20,
    to: 25,
    source: "x",
    display: false,
    multilineInline: false,
    raw: inline("x")
  },
  ...structuralRanges
];
const inlineState = {
  selection: { ranges: [{ from: 0, to: 0 }] },
  field(field) {
    if (field === livePreviewField) return true;
    if (field === mathRangesField) return inlineRanges;
    return false;
  }
};
decorations = buildInlineMathDecorations(
  {
    state: inlineState,
    visibleRanges: [{ from: 0, to: 100 }]
  },
  mathRangesField
);
assert.equal(decorations.length, 1);
assert.equal(decorations[0].from, 20);
assert.equal(decorations[0].to, 25);

console.log("latex-delimiter-compat tests passed");
