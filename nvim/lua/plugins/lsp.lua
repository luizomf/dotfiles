return {
	{
		"neovim/nvim-lspconfig",
		dependencies = {
			"williamboman/mason-lspconfig.nvim",
			"hrsh7th/cmp-nvim-lsp",
		},
		config = function()
			local capabilities = require("cmp_nvim_lsp").default_capabilities()

			local on_attach = function(client, bufnr)
				local map = vim.keymap.set
				local opts = { buffer = bufnr, noremap = true, silent = true }

				map("n", "gd", vim.lsp.buf.definition, opts)
				map("n", "K", vim.lsp.buf.hover, opts)
				map("n", "<leader>rn", vim.lsp.buf.rename, opts)
				map("n", "<leader>ca", vim.lsp.buf.code_action, opts)

				if client.server_capabilities.documentFormattingProvider then
					-- A formatação agora é feita pelo conform.nvim
				end
			end

			require("mason-lspconfig").setup({
				handlers = {
					function(server_name)
						local server_opts = {
							on_attach = on_attach,
							capabilities = capabilities,
						}

						if server_name == "pyright" then
							-- Desabilita o linting do pyright para usar o ruff
							server_opts.settings = {
								pyright = {
									disableOrganizeImports = true,
								},
								python = {
									analysis = {
										ignore = { "*" },
									},
								},
							}
						end

						require("lspconfig")[server_name].setup(server_opts)
					end,
				},
			})
		end,
	},
}
