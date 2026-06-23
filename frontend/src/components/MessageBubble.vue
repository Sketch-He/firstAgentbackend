<script setup lang="ts">
import { computed, ref } from "vue";
import { parseMarkdown } from "../lib/markdown";
import type { ChatMessage } from "../types/chat";

const props = defineProps<{
  message: ChatMessage;
}>();

const copyState = ref<"idle" | "copied" | "failed">("idle");

const roleTextMap: Record<ChatMessage["role"], string> = {
  system: "系统",
  user: "用户",
  assistant: "助手",
  tool: "工具"
};

const renderedBlocks = computed(() => parseMarkdown(props.message.content));

function getHeadingTag(level: 1 | 2 | 3 | 4 | 5 | 6) {
  return `h${level}` as const;
}

async function copyCode(code: string) {
  try {
    await navigator.clipboard.writeText(code);
    copyState.value = "copied";
  } catch {
    copyState.value = "failed";
  }

  window.setTimeout(() => {
    copyState.value = "idle";
  }, 1800);
}
</script>

<template>
  <article :class="['message-bubble', message.role]">
    <p class="message-role">{{ roleTextMap[message.role] }}</p>
    <div class="message-content markdown-content">
      <template v-if="message.content.trim()">
        <template v-for="(block, index) in renderedBlocks" :key="`${message.id}-${index}`">
          <component
            :is="getHeadingTag(block.level)"
            v-if="block.type === 'heading'"
            class="markdown-heading"
            v-html="block.html"
          />

          <p
            v-else-if="block.type === 'paragraph'"
            class="markdown-paragraph"
            v-html="block.html"
          />

          <blockquote
            v-else-if="block.type === 'blockquote'"
            class="markdown-blockquote"
            v-html="block.html"
          />

          <ul
            v-else-if="block.type === 'unordered-list'"
            class="markdown-list"
          >
            <li v-for="(item, itemIndex) in block.items" :key="itemIndex" v-html="item" />
          </ul>

          <ol
            v-else-if="block.type === 'ordered-list'"
            class="markdown-list markdown-list-ordered"
          >
            <li v-for="(item, itemIndex) in block.items" :key="itemIndex" v-html="item" />
          </ol>

          <div v-else-if="block.type === 'code'" class="code-block-shell">
            <div class="code-block-header">
              <span>{{ block.language || "plain text" }}</span>
              <button
                type="button"
                class="code-copy-button"
                @click="copyCode(block.code)"
              >
                {{
                  copyState === "copied"
                    ? "已复制"
                    : copyState === "failed"
                      ? "复制失败"
                      : "复制代码"
                }}
              </button>
            </div>
            <pre class="code-block"><code>{{ block.code }}</code></pre>
          </div>
        </template>
      </template>

      <p v-else class="message-placeholder">正在等待内容...</p>
    </div>
  </article>
</template>
