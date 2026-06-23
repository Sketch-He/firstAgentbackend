function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function sanitizeUrl(url: string): string | null {
  const trimmedUrl = url.trim();

  if (!trimmedUrl) {
    return null;
  }

  if (/^mailto:/i.test(trimmedUrl)) {
    return trimmedUrl;
  }

  try {
    const parsedUrl = new URL(trimmedUrl);

    if (parsedUrl.protocol === "http:" || parsedUrl.protocol === "https:") {
      return parsedUrl.toString();
    }
  } catch {
    return null;
  }

  return null;
}

interface InlineTextNode {
  type: "text";
  content: string;
}

interface InlineCodeNode {
  type: "code";
  content: string;
}

interface InlineStrongNode {
  type: "strong";
  children: InlineNode[];
}

interface InlineEmphasisNode {
  type: "em";
  children: InlineNode[];
}

interface InlineLinkNode {
  type: "link";
  href: string;
  children: InlineNode[];
}

type InlineNode =
  | InlineTextNode
  | InlineCodeNode
  | InlineStrongNode
  | InlineEmphasisNode
  | InlineLinkNode;

export interface MarkdownParagraphBlock {
  type: "paragraph";
  html: string;
}

export interface MarkdownHeadingBlock {
  type: "heading";
  level: 1 | 2 | 3 | 4 | 5 | 6;
  html: string;
}

export interface MarkdownListBlock {
  type: "unordered-list" | "ordered-list";
  items: string[];
}

export interface MarkdownBlockquoteBlock {
  type: "blockquote";
  html: string;
}

export interface MarkdownCodeBlock {
  type: "code";
  language: string;
  code: string;
}

export type MarkdownBlock =
  | MarkdownParagraphBlock
  | MarkdownHeadingBlock
  | MarkdownListBlock
  | MarkdownBlockquoteBlock
  | MarkdownCodeBlock;

interface InlineParseResult {
  closed: boolean;
  index: number;
  nodes: InlineNode[];
}

function renderInlineNodes(nodes: InlineNode[]): string {
  return nodes
    .map((node) => {
      if (node.type === "text") {
        return escapeHtml(node.content).replace(/\n/g, "<br />");
      }

      if (node.type === "code") {
        return `<code>${escapeHtml(node.content)}</code>`;
      }

      if (node.type === "strong") {
        return `<strong>${renderInlineNodes(node.children)}</strong>`;
      }

      if (node.type === "em") {
        return `<em>${renderInlineNodes(node.children)}</em>`;
      }

      return `<a href="${escapeHtml(node.href)}" target="_blank" rel="noreferrer">${renderInlineNodes(node.children)}</a>`;
    })
    .join("");
}

function parseInlineRange(text: string, startIndex = 0, stopToken?: string): InlineParseResult {
  const nodes: InlineNode[] = [];
  let cursor = startIndex;
  let textBuffer = "";

  const pushText = () => {
    if (!textBuffer) {
      return;
    }

    nodes.push({
      type: "text",
      content: textBuffer
    });
    textBuffer = "";
  };

  while (cursor < text.length) {
    if (stopToken && text.startsWith(stopToken, cursor)) {
      pushText();
      return {
        closed: true,
        index: cursor + stopToken.length,
        nodes
      };
    }

    if (text[cursor] === "`") {
      const closingIndex = text.indexOf("`", cursor + 1);

      if (closingIndex !== -1) {
        pushText();
        nodes.push({
          type: "code",
          content: text.slice(cursor + 1, closingIndex)
        });
        cursor = closingIndex + 1;
        continue;
      }
    }

    if (text.startsWith("**", cursor)) {
      const strongResult = parseInlineRange(text, cursor + 2, "**");

      if (strongResult.closed) {
        pushText();
        nodes.push({
          type: "strong",
          children: strongResult.nodes
        });
        cursor = strongResult.index;
        continue;
      }
    }

    if (text[cursor] === "*" || text[cursor] === "_") {
      const emphasisMarker = text[cursor];
      const emphasisResult = parseInlineRange(text, cursor + 1, emphasisMarker);

      if (emphasisResult.closed) {
        pushText();
        nodes.push({
          type: "em",
          children: emphasisResult.nodes
        });
        cursor = emphasisResult.index;
        continue;
      }
    }

    if (text[cursor] === "[") {
      const labelEndIndex = text.indexOf("]", cursor + 1);

      if (
        labelEndIndex !== -1 &&
        text[labelEndIndex + 1] === "("
      ) {
        const urlEndIndex = text.indexOf(")", labelEndIndex + 2);

        if (urlEndIndex !== -1) {
          const href = sanitizeUrl(text.slice(labelEndIndex + 2, urlEndIndex));

          if (href) {
            pushText();
            nodes.push({
              type: "link",
              href,
              children: parseInlineRange(text.slice(cursor + 1, labelEndIndex)).nodes
            });
            cursor = urlEndIndex + 1;
            continue;
          }
        }
      }
    }

    textBuffer += text[cursor];
    cursor += 1;
  }

  pushText();

  return {
    closed: false,
    index: cursor,
    nodes
  };
}

function renderInlineMarkdown(text: string): string {
  return renderInlineNodes(parseInlineRange(text).nodes);
}

function isBlockBoundary(line: string): boolean {
  return (
    !line.trim() ||
    /^#{1,6}\s+/.test(line) ||
    /^```/.test(line) ||
    /^>\s?/.test(line) ||
    /^[-*+]\s+/.test(line) ||
    /^\d+\.\s+/.test(line)
  );
}

export function parseMarkdown(content: string): MarkdownBlock[] {
  const lines = content.replace(/\r\n?/g, "\n").split("\n");
  const blocks: MarkdownBlock[] = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];

    if (!line.trim()) {
      index += 1;
      continue;
    }

    const codeFenceMatch = line.match(/^```([\w.-]*)\s*$/);

    if (codeFenceMatch) {
      const codeLines: string[] = [];
      index += 1;

      while (index < lines.length && !/^```/.test(lines[index])) {
        codeLines.push(lines[index]);
        index += 1;
      }

      if (index < lines.length && /^```/.test(lines[index])) {
        index += 1;
      }

      blocks.push({
        type: "code",
        language: codeFenceMatch[1] ?? "",
        code: codeLines.join("\n")
      });
      continue;
    }

    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);

    if (headingMatch) {
      blocks.push({
        type: "heading",
        level: headingMatch[1].length as 1 | 2 | 3 | 4 | 5 | 6,
        html: renderInlineMarkdown(headingMatch[2])
      });
      index += 1;
      continue;
    }

    if (/^[-*+]\s+/.test(line)) {
      const items: string[] = [];

      while (index < lines.length) {
        const listMatch = lines[index].match(/^[-*+]\s+(.*)$/);

        if (!listMatch) {
          break;
        }

        items.push(renderInlineMarkdown(listMatch[1]));
        index += 1;
      }

      blocks.push({
        type: "unordered-list",
        items
      });
      continue;
    }

    if (/^\d+\.\s+/.test(line)) {
      const items: string[] = [];

      while (index < lines.length) {
        const listMatch = lines[index].match(/^\d+\.\s+(.*)$/);

        if (!listMatch) {
          break;
        }

        items.push(renderInlineMarkdown(listMatch[1]));
        index += 1;
      }

      blocks.push({
        type: "ordered-list",
        items
      });
      continue;
    }

    if (/^>\s?/.test(line)) {
      const quoteLines: string[] = [];

      while (index < lines.length) {
        const quoteMatch = lines[index].match(/^>\s?(.*)$/);

        if (!quoteMatch) {
          break;
        }

        quoteLines.push(quoteMatch[1]);
        index += 1;
      }

      blocks.push({
        type: "blockquote",
        html: renderInlineMarkdown(quoteLines.join("\n"))
      });
      continue;
    }

    const paragraphLines: string[] = [];

    while (index < lines.length && !isBlockBoundary(lines[index])) {
      paragraphLines.push(lines[index]);
      index += 1;
    }

    if (paragraphLines.length > 0) {
      blocks.push({
        type: "paragraph",
        html: renderInlineMarkdown(paragraphLines.join("\n"))
      });
    }
  }

  return blocks;
}
