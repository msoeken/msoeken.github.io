hljs.registerLanguage("qsharp", function(hljs) {
  return {
      keywords: {
          keyword: 'operation function let using for if in',
          type: 'Int Qubit Bool Unit',
          built_in: 'H HY RFrac CNOT PauliZ'
      },
      contains: [
          hljs.C_LINE_COMMENT_MODE,
          hljs.NUMBER_MODE,
      ]
  }
});
hljs.initHighlightingOnLoad();
