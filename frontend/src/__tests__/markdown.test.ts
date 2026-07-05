import { describe, it, expect } from "vitest";
import { parseMarkdown } from "../lib/markdown";

describe("parseMarkdown", () => {
  describe("段落", () => {
    it("解析普通段落", () => {
      const result = parseMarkdown("Hello World");
      expect(result).toHaveLength(1);
      expect(result[0].type).toBe("paragraph");
    });

    it("解析多个段落", () => {
      const result = parseMarkdown("段落1\n\n段落2");
      expect(result).toHaveLength(2);
    });
  });

  describe("标题", () => {
    it("解析一级标题", () => {
      const result = parseMarkdown("# 标题");
      expect(result).toHaveLength(1);
      expect(result[0].type).toBe("heading");
      if (result[0].type === "heading") {
        expect(result[0].level).toBe(1);
      }
    });

    it("解析多级标题", () => {
      const result = parseMarkdown("## 二级标题\n### 三级标题");
      expect(result).toHaveLength(2);
    });
  });

  describe("代码块", () => {
    it("解析 fenced code block", () => {
      const input = '```python\nprint("hello")\n```';
      const result = parseMarkdown(input);
      expect(result).toHaveLength(1);
      expect(result[0].type).toBe("code");
      if (result[0].type === "code") {
        expect(result[0].language).toBe("python");
        expect(result[0].code).toContain('print("hello")');
      }
    });

    it("解析无语言的 code block", () => {
      const input = "```\ncode\n```";
      const result = parseMarkdown(input);
      expect(result).toHaveLength(1);
      expect(result[0].type).toBe("code");
    });
  });

  describe("列表", () => {
    it("解析无序列表", () => {
      const result = parseMarkdown("- 项目1\n- 项目2\n- 项目3");
      expect(result).toHaveLength(1);
      expect(result[0].type).toBe("unordered-list");
      if (result[0].type === "unordered-list") {
        expect(result[0].items).toHaveLength(3);
      }
    });

    it("解析有序列表", () => {
      const result = parseMarkdown("1. 第一\n2. 第二\n3. 第三");
      expect(result).toHaveLength(1);
      expect(result[0].type).toBe("ordered-list");
    });
  });

  describe("引用", () => {
    it("解析 blockquote", () => {
      const result = parseMarkdown("> 这是引用");
      expect(result).toHaveLength(1);
      expect(result[0].type).toBe("blockquote");
    });
  });

  describe("空内容", () => {
    it("处理空字符串", () => {
      const result = parseMarkdown("");
      expect(result).toHaveLength(0);
    });

    it("处理纯空白", () => {
      const result = parseMarkdown("   \n\n   ");
      expect(result).toHaveLength(0);
    });
  });
});
