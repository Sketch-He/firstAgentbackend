import { describe, it, expect, vi, beforeEach } from "vitest";
import { ApiError } from "../lib/chatApi";

// Mock fetch
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

// Mock cookie utility
vi.mock("../utils/cookie", () => ({
  getUserId: () => "test-user-id",
}));

describe("ApiError", () => {
  it("创建错误实例", () => {
    const error = new ApiError(10001, "Not Found");
    expect(error.code).toBe(10001);
    expect(error.message).toBe("Not Found");
    expect(error.name).toBe("ApiError");
  });

  it("是 Error 的实例", () => {
    const error = new ApiError(0, "ok");
    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(ApiError);
  });
});

describe("chatApi", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  // 注意：由于 chatApi 使用了模块级的 apiBaseUrl，
  // 在测试环境中需要特殊处理才能正确测试。
  // 这里主要测试错误处理逻辑。

  it("ApiError 可以被 catch 捕获", () => {
    const error = new ApiError(10002, "Bad Request");
    try {
      throw error;
    } catch (e) {
      expect(e).toBeInstanceOf(ApiError);
      if (e instanceof ApiError) {
        expect(e.code).toBe(10002);
      }
    }
  });
});
