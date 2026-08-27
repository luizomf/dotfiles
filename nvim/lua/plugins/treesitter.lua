return {
  {
    "nvim-treesitter/nvim-treesitter",
    branch = "main",
    lazy = false,
    build = ":TSUpdate",
    config = function()
      -- tmux is no longer bundled on the main branch, but remains maintained.
      vim.api.nvim_create_autocmd("User", {
        pattern = "TSUpdate",
        callback = function()
          require("nvim-treesitter.parsers").tmux = {
            install_info = {
              url = "https://github.com/Freed-Wu/tree-sitter-tmux",
              revision = "58147321fa1f00daec15dd4d371bc9e2e9373459",
              generate = true,
              generate_from_json = false,
              queries = "queries",
            },
          }
        end,
      })

      require("nvim-treesitter").setup()

      -- Install parsers
      require("nvim-treesitter").install({
        "c",
        "cpp",
        "go",
        "rust",
        "just",
        "cmake",
        "bash",
        "tmux",
        "zsh",
        "ssh_config",
        "dockerfile",
        "editorconfig",
        "lua",
        "vim",
        "vimdoc",
        "html",
        "xml",
        "css",
        "scss",
        "styled",
        "javascript",
        "typescript",
        "tsx",
        "jsx",
        "json",
        "yaml",
        "toml",
        "htmldjango",
        "passwd",
        "terraform",
        "markdown",
        "markdown_inline",
        "python",
        "astro",
      })

      -- Enable treesitter highlighting and indentation for all filetypes
      vim.api.nvim_create_autocmd("FileType", {
        callback = function()
          pcall(vim.treesitter.start)
          vim.bo.indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
        end,
      })
    end,
  },
  {
    "nvim-treesitter/nvim-treesitter-textobjects",
    branch = "main",
    lazy = false,
    dependencies = { "nvim-treesitter/nvim-treesitter" },
    config = function()
      require("nvim-treesitter-textobjects").setup({
        select = {
          lookahead = true,
        },
        move = {
          set_jumps = true,
        },
      })

      -- Select keymaps
      vim.keymap.set({ "x", "o" }, "af", function()
        require("nvim-treesitter-textobjects.select").select_textobject(
          "@function.outer",
          "textobjects"
        )
      end)
      vim.keymap.set({ "x", "o" }, "if", function()
        require("nvim-treesitter-textobjects.select").select_textobject(
          "@function.inner",
          "textobjects"
        )
      end)
      vim.keymap.set({ "x", "o" }, "ac", function()
        require("nvim-treesitter-textobjects.select").select_textobject(
          "@class.outer",
          "textobjects"
        )
      end)
      vim.keymap.set({ "x", "o" }, "ic", function()
        require("nvim-treesitter-textobjects.select").select_textobject(
          "@class.inner",
          "textobjects"
        )
      end)
      vim.keymap.set({ "x", "o" }, "as", function()
        require("nvim-treesitter-textobjects.select").select_textobject(
          "@local.scope",
          "locals"
        )
      end)

      -- Move keymaps
      vim.keymap.set({ "n", "x", "o" }, "]f", function()
        require("nvim-treesitter-textobjects.move").goto_next_start(
          "@function.outer",
          "textobjects"
        )
      end)
      vim.keymap.set({ "n", "x", "o" }, "]c", function()
        require("nvim-treesitter-textobjects.move").goto_next_start(
          "@class.outer",
          "textobjects"
        )
      end)
      vim.keymap.set({ "n", "x", "o" }, "[f", function()
        require("nvim-treesitter-textobjects.move").goto_previous_start(
          "@function.outer",
          "textobjects"
        )
      end)
      vim.keymap.set({ "n", "x", "o" }, "[c", function()
        require("nvim-treesitter-textobjects.move").goto_previous_start(
          "@class.outer",
          "textobjects"
        )
      end)
    end,
  },
  {
    "windwp/nvim-ts-autotag",
  },
}
