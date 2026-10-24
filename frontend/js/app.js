
"use strict";

// Endereço do backend FastAPI.
const API_URL = "http://127.0.0.1:8000";
const TOKEN_KEY = "access_token";

// Estado da aplicação.
let clientes = [];
let veiculos = [];
let usuarioLogado = null;
let carregandoClientes = false;
let carregandoVeiculos = false;

// Elementos de autenticação.
const loginOverlay = document.getElementById("login-overlay");
const appContainer = document.getElementById("app-container");
const formLogin = document.getElementById("form-login");
const campoLogin = document.getElementById("login-usuario");
const campoSenha = document.getElementById("login-senha");
const mensagemLogin = document.getElementById("login-mensagem");
const botaoLogin = document.getElementById("btn-login");
const botaoLogout = document.getElementById("btn-logout");

// Elementos de clientes.
const formCliente = document.getElementById("form-cliente");
const campoClienteId = document.getElementById("cliente-id");
const campoNome = document.getElementById("cliente-nome");
const campoDocumento = document.getElementById("cliente-documento");
const campoTelefone = document.getElementById("cliente-telefone");
const campoEmail = document.getElementById("cliente-email");
const mensagemCliente = document.getElementById("cliente-mensagem");
const mensagemLista = document.getElementById("lista-mensagem");
const tabelaClientes = document.getElementById("tabela-clientes");
const pesquisaCliente = document.getElementById("pesquisa-cliente");
const botaoSalvarCliente = document.getElementById("btn-salvar-cliente");
const botaoCancelarEdicao = document.getElementById("btn-cancelar-edicao");
const botaoAtualizarClientes = document.getElementById("btn-atualizar-clientes");

// Elementos de veículos.
const formVeiculo = document.getElementById("form-veiculo");
const campoVeiculoId = document.getElementById("veiculo-id");
const campoVeiculoPlaca = document.getElementById("veiculo-placa");
const campoVeiculoTipo = document.getElementById("veiculo-tipo");
const campoVeiculoModelo = document.getElementById("veiculo-modelo");
const campoVeiculoCor = document.getElementById("veiculo-cor");
const campoVeiculoCliente = document.getElementById("veiculo-cliente");
const mensagemVeiculo = document.getElementById("veiculo-mensagem");
const mensagemListaVeiculos = document.getElementById("veiculo-lista-mensagem");
const tabelaVeiculos = document.getElementById("tabela-veiculos");
const pesquisaVeiculo = document.getElementById("pesquisa-veiculo");
const botaoSalvarVeiculo = document.getElementById("btn-salvar-veiculo");
const botaoCancelarVeiculo = document.getElementById("btn-cancelar-veiculo");
const botaoAtualizarVeiculos = document.getElementById("btn-atualizar-veiculos");

// Exibe mensagens sem interpretar o conteúdo como HTML.
function mostrarMensagem(elemento, texto, tipo = "info") {
    if (!elemento) return;

    elemento.textContent = texto || "";
    elemento.className = "message";

    if (texto) elemento.classList.add(tipo);
}

// Converte erros da API em mensagens compreensíveis.
async function obterMensagemErro(resposta) {
    try {
        const dados = await resposta.json();

        if (typeof dados.detail === "string") return dados.detail;

        if (Array.isArray(dados.detail)) {
            return dados.detail
                .map((erro) => erro.msg || "Dados inválidos.")
                .join(" ");
        }

        return "Não foi possível concluir a operação.";
    } catch {
        return `Erro na requisição. Código HTTP: ${resposta.status}.`;
    }
}

// Função central para chamadas autenticadas à API.
async function requisicaoAPI(caminho, opcoes = {}) {
    const token = localStorage.getItem(TOKEN_KEY);
    const headers = new Headers(opcoes.headers || {});

    if (token) headers.set("Authorization", `Bearer ${token}`);

    if (opcoes.body && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
    }

    let resposta;

    try {
        resposta = await fetch(`${API_URL}${caminho}`, {
            ...opcoes,
            headers
        });
    } catch {
        throw new Error(
            "Não foi possível conectar ao backend. Verifique se a API está rodando e se o endereço está correto."
        );
    }

    if (resposta.status === 401) {
        encerrarSessao(
            "Sua sessão expirou ou não é válida. Faça login novamente."
        );
        throw new Error("Sessão inválida.");
    }

    if (resposta.status === 403) {
        throw new Error("Você não tem permissão para executar esta operação.");
    }

    if (!resposta.ok) {
        throw new Error(await obterMensagemErro(resposta));
    }

    if (resposta.status === 204) return null;

    const tipoConteudo = resposta.headers.get("content-type") || "";

    if (tipoConteudo.includes("application/json")) {
        return resposta.json();
    }

    return null;
}

// Exibe a tela de login.
function mostrarTelaLogin(mensagem = "") {
    loginOverlay.hidden = false;
    appContainer.hidden = true;

    mostrarMensagem(
        mensagemLogin,
        mensagem,
        mensagem ? "error" : "info"
    );

    campoLogin.focus();
}

// Exibe o sistema após autenticação.
function mostrarSistema(usuario) {
    usuarioLogado = usuario;

    loginOverlay.hidden = true;
    appContainer.hidden = false;

    document.getElementById("usuario-nome").textContent =
        usuario?.nome || usuario?.nome_completo || usuario?.login || "Usuário";

    mostrarMensagem(mensagemLogin, "");
}

// Finaliza a sessão local.
function encerrarSessao(mensagem = "") {
    localStorage.removeItem(TOKEN_KEY);

    usuarioLogado = null;
    clientes = [];
    veiculos = [];

    if (tabelaClientes) tabelaClientes.replaceChildren();
    if (tabelaVeiculos) tabelaVeiculos.replaceChildren();

    if (formCliente) formCliente.reset();
    if (formVeiculo) formVeiculo.reset();

    if (campoClienteId) campoClienteId.value = "";
    if (campoVeiculoId) campoVeiculoId.value = "";

    atualizarModoFormularioCliente(false);
    atualizarModoFormularioVeiculo(false);
    atualizarIndicadores();

    mostrarTelaLogin(mensagem);
}

// Realiza login.
async function fazerLogin(evento) {
    evento.preventDefault();

    const login = campoLogin.value.trim();
    const senha = campoSenha.value;

    if (!login || !senha) {
        mostrarMensagem(mensagemLogin, "Informe o login e a senha.", "error");
        return;
    }

    botaoLogin.disabled = true;
    botaoLogin.textContent = "Entrando...";
    mostrarMensagem(mensagemLogin, "");

    try {
        const resposta = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ login, senha })
        });

        if (!resposta.ok) {
            throw new Error(await obterMensagemErro(resposta));
        }

        const dados = await resposta.json();

        if (!dados.access_token) {
            throw new Error("O backend não retornou o campo access_token.");
        }

        localStorage.setItem(TOKEN_KEY, dados.access_token);

        const usuario = await requisicaoAPI("/auth/eu");

        mostrarSistema(usuario);
        campoSenha.value = "";
        navegarPara("inicio");

        await Promise.all([
            carregarClientes(),
            carregarVeiculos()
        ]);
    } catch (erro) {
        localStorage.removeItem(TOKEN_KEY);

        mostrarMensagem(
            mensagemLogin,
            erro.message === "Sessão inválida."
                ? "Não foi possível validar a sessão. Confira o backend e tente novamente."
                : erro.message,
            "error"
        );
    } finally {
        botaoLogin.disabled = false;
        botaoLogin.textContent = "Entrar";
    }
}

// Verifica se há sessão salva.
async function verificarSessaoSalva() {
    if (!localStorage.getItem(TOKEN_KEY)) {
        mostrarTelaLogin();
        return;
    }

    mostrarMensagem(mensagemLogin, "Verificando sua sessão...", "info");

    try {
        const usuario = await requisicaoAPI("/auth/eu");

        mostrarSistema(usuario);
        navegarPara("inicio");

        await Promise.all([
            carregarClientes(),
            carregarVeiculos()
        ]);
    } catch (erro) {
        if (localStorage.getItem(TOKEN_KEY)) {
            localStorage.removeItem(TOKEN_KEY);
        }

        mostrarTelaLogin(
            erro.message === "Sessão inválida."
                ? "Sua sessão expirou. Entre novamente."
                : erro.message
        );
    }
}

// Navegação entre páginas.
function navegarPara(pagina) {
    const permitidas = [
        "inicio",
        "clientes",
        "veiculos",
        "movimentacoes"
    ];

    if (!permitidas.includes(pagina)) pagina = "inicio";

    document.querySelectorAll(".page-section").forEach((secao) => {
        secao.hidden = secao.id !== `pagina-${pagina}`;
    });

    document.querySelectorAll(".nav-link").forEach((link) => {
        const ativo = link.dataset.page === pagina;

        link.classList.toggle("active", ativo);

        if (ativo) link.setAttribute("aria-current", "page");
        else link.removeAttribute("aria-current");
    });

    const nomes = {
        inicio: { titulo: "Visão geral", breadcrumb: "Início" },
        clientes: { titulo: "Gestão de clientes", breadcrumb: "Clientes" },
        veiculos: { titulo: "Veículos", breadcrumb: "Veículos" },
        movimentacoes: {
            titulo: "Entradas e saídas",
            breadcrumb: "Entradas e saídas"
        }
    };

    document.getElementById("titulo-pagina").textContent = nomes[pagina].titulo;
    document.getElementById("pagina-atual").textContent = nomes[pagina].breadcrumb;

    if (pagina === "veiculos" && localStorage.getItem(TOKEN_KEY)) {
        carregarVeiculos();
        carregarOpcoesClientes();
    }

    if (pagina === "clientes" && localStorage.getItem(TOKEN_KEY)) {
        carregarClientes();
    }
}

// Aceita respostas de listagem comuns.
function extrairLista(dados, nomeLista, descricao) {
    if (Array.isArray(dados)) return dados;
    if (dados && Array.isArray(dados.items)) return dados.items;
    if (dados && Array.isArray(dados[nomeLista])) return dados[nomeLista];

    throw new Error(
        `A resposta da rota de ${descricao} não contém uma lista reconhecida.`
    );
}

// =========================
// CLIENTES
// =========================

async function carregarClientes() {
    if (carregandoClientes) return;

    carregandoClientes = true;
    mostrarMensagem(mensagemLista, "Carregando clientes...", "info");

    try {
        clientes = extrairLista(
            await requisicaoAPI("/clientes/"),
            "clientes",
            "clientes"
        );

        renderizarClientes();
        atualizarIndicadores();
        atualizarSelectClientes();

        mostrarMensagem(
            mensagemLista,
            `${clientes.length} cliente(s) carregado(s).`,
            "success"
        );
    } catch (erro) {
        if (erro.message !== "Sessão inválida.") {
            mostrarMensagem(mensagemLista, erro.message, "error");
        }
    } finally {
        carregandoClientes = false;
    }
}

function criarCelula(texto) {
    const celula = document.createElement("td");
    celula.textContent = texto ?? "—";
    return celula;
}

function clienteEstaAtivo(cliente) {
    if (cliente.ativo === undefined || cliente.ativo === null) return true;

    return cliente.ativo === true ||
        cliente.ativo === 1 ||
        cliente.ativo === "1" ||
        cliente.ativo === "true";
}

function renderizarClientes() {
    tabelaClientes.replaceChildren();

    const termo = pesquisaCliente.value.trim().toLocaleLowerCase("pt-BR");

    const filtrados = clientes.filter((cliente) => {
        const conteudo = [
            cliente.nome,
            cliente.cpf_cnpj,
            cliente.telefone,
            cliente.email,
            cliente.id
        ]
            .map((valor) => String(valor ?? ""))
            .join(" ")
            .toLocaleLowerCase("pt-BR");

        return conteudo.includes(termo);
    });

    if (filtrados.length === 0) {
        const linha = document.createElement("tr");
        const celula = document.createElement("td");

        celula.colSpan = 7;
        celula.className = "empty-state";
        celula.textContent = termo
            ? "Nenhum cliente corresponde à pesquisa."
            : "Nenhum cliente cadastrado.";

        linha.appendChild(celula);
        tabelaClientes.appendChild(linha);
        return;
    }

    filtrados.forEach((cliente) => {
        const linha = document.createElement("tr");

        linha.append(
            criarCelula(cliente.id),
            criarCelula(cliente.nome),
            criarCelula(cliente.cpf_cnpj),
            criarCelula(cliente.telefone),
            criarCelula(cliente.email)
        );

        const celulaStatus = document.createElement("td");
        const etiqueta = document.createElement("span");
        const ativo = clienteEstaAtivo(cliente);

        etiqueta.className = ativo
            ? "status-badge status-active"
            : "status-badge status-inactive";

        etiqueta.textContent = ativo ? "Ativo" : "Inativo";
        celulaStatus.appendChild(etiqueta);
        linha.appendChild(celulaStatus);

        const celulaAcoes = document.createElement("td");
        const grupo = document.createElement("div");
        grupo.className = "table-actions";

        const editar = document.createElement("button");
        editar.type = "button";
        editar.className = "btn-small";
        editar.textContent = "Editar";
        editar.addEventListener("click", () => editarCliente(cliente));

        const excluir = document.createElement("button");
        excluir.type = "button";
        excluir.className = "btn-small danger";
        excluir.textContent = "Excluir";
        excluir.addEventListener("click", () => excluirCliente(cliente));

        grupo.append(editar, excluir);
        celulaAcoes.appendChild(grupo);
        linha.appendChild(celulaAcoes);

        tabelaClientes.appendChild(linha);
    });
}

function atualizarIndicadores() {
    const ativos = clientes.filter(clienteEstaAtivo).length;

    document.getElementById("total-clientes").textContent = clientes.length;
    document.getElementById("clientes-ativos").textContent = ativos;
    document.getElementById("clientes-inativos").textContent = clientes.length - ativos;
}

function atualizarModoFormularioCliente(editando) {
    document.getElementById("titulo-form-cliente").textContent =
        editando ? "Editar cliente" : "Cadastrar cliente";

    botaoSalvarCliente.textContent =
        editando ? "Salvar alterações" : "Cadastrar cliente";

    botaoCancelarEdicao.hidden = !editando;
}

function limparFormularioCliente() {
    formCliente.reset();
    campoClienteId.value = "";
    atualizarModoFormularioCliente(false);
    mostrarMensagem(mensagemCliente, "");
}

function editarCliente(cliente) {
    campoClienteId.value = cliente.id ?? "";
    campoNome.value = cliente.nome ?? "";
    campoDocumento.value = cliente.cpf_cnpj ?? "";
    campoTelefone.value = cliente.telefone ?? "";
    campoEmail.value = cliente.email ?? "";

    atualizarModoFormularioCliente(true);

    mostrarMensagem(
        mensagemCliente,
        `Editando o cadastro de ${cliente.nome || "cliente"}.`,
        "info"
    );

    navegarPara("clientes");
    campoNome.focus();

    formCliente.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

function obterDadosFormularioCliente() {
    const nome = campoNome.value.trim();
    const documento = campoDocumento.value.trim();
    const telefone = campoTelefone.value.trim();
    const email = campoEmail.value.trim();

    if (!nome) throw new Error("Informe o nome do cliente.");
    if (!documento) throw new Error("Informe o CPF ou CNPJ do cliente.");

    return {
        nome,
        cpf_cnpj: documento,
        telefone: telefone || null,
        email: email || null
    };
}

async function salvarCliente(evento) {
    evento.preventDefault();

    let dados;

    try {
        dados = obterDadosFormularioCliente();
    } catch (erro) {
        mostrarMensagem(mensagemCliente, erro.message, "error");
        return;
    }

    const id = campoClienteId.value.trim();
    const editando = Boolean(id);

    botaoSalvarCliente.disabled = true;
    botaoSalvarCliente.textContent = editando ? "Salvando..." : "Cadastrando...";
    mostrarMensagem(mensagemCliente, "");

    try {
        await requisicaoAPI(
            editando ? `/clientes/${encodeURIComponent(id)}` : "/clientes/",
            {
                method: editando ? "PATCH" : "POST",
                body: JSON.stringify(dados)
            }
        );

        limparFormularioCliente();

        mostrarMensagem(
            mensagemCliente,
            editando
                ? "Cliente atualizado com sucesso."
                : "Cliente cadastrado com sucesso.",
            "success"
        );

        await carregarClientes();
    } catch (erro) {
        if (erro.message !== "Sessão inválida.") {
            mostrarMensagem(mensagemCliente, erro.message, "error");
        }
    } finally {
        botaoSalvarCliente.disabled = false;
        botaoSalvarCliente.textContent = campoClienteId.value
            ? "Salvar alterações"
            : "Cadastrar cliente";
    }
}

async function excluirCliente(cliente) {
    if (cliente.id === undefined || cliente.id === null) {
        mostrarMensagem(
            mensagemLista,
            "Não foi possível identificar o ID deste cliente.",
            "error"
        );
        return;
    }

    if (!window.confirm(`Deseja realmente excluir o cliente "${cliente.nome}"?`)) {
        return;
    }

    mostrarMensagem(mensagemLista, "Excluindo cliente...", "info");

    try {
        await requisicaoAPI(
            `/clientes/${encodeURIComponent(cliente.id)}`,
            { method: "DELETE" }
        );

        if (String(campoClienteId.value) === String(cliente.id)) {
            limparFormularioCliente();
        }

        mostrarMensagem(mensagemLista, "Cliente excluído com sucesso.", "success");
        await carregarClientes();
    } catch (erro) {
        if (erro.message !== "Sessão inválida.") {
            mostrarMensagem(mensagemLista, erro.message, "error");
        }
    }
}

// Atualiza o select de clientes do formulário de veículos.
function atualizarSelectClientes() {
    if (!campoVeiculoCliente) return;

    const valorAtual = campoVeiculoCliente.value;
    campoVeiculoCliente.replaceChildren();

    const opcaoVazia = document.createElement("option");
    opcaoVazia.value = "";
    opcaoVazia.textContent = "Sem cliente vinculado";
    campoVeiculoCliente.appendChild(opcaoVazia);

    clientes.filter(clienteEstaAtivo).forEach((cliente) => {
        const opcao = document.createElement("option");
        opcao.value = String(cliente.id);
        opcao.textContent = `${cliente.nome} (ID ${cliente.id})`;
        campoVeiculoCliente.appendChild(opcao);
    });

    if ([...campoVeiculoCliente.options].some((opcao) => opcao.value === valorAtual)) {
        campoVeiculoCliente.value = valorAtual;
    }
}

async function carregarOpcoesClientes() {
    if (!clientes.length) {
        await carregarClientes();
    } else {
        atualizarSelectClientes();
    }
}

// =========================
// VEÍCULOS
// =========================

async function carregarVeiculos() {
    if (carregandoVeiculos) return;

    carregandoVeiculos = true;
    mostrarMensagem(mensagemListaVeiculos, "Carregando veículos...", "info");

    try {
        veiculos = extrairLista(
            await requisicaoAPI("/veiculos/"),
            "veiculos",
            "veículos"
        );

        renderizarVeiculos();

        mostrarMensagem(
            mensagemListaVeiculos,
            `${veiculos.length} veículo(s) carregado(s).`,
            "success"
        );
    } catch (erro) {
        if (erro.message !== "Sessão inválida.") {
            mostrarMensagem(mensagemListaVeiculos, erro.message, "error");
        }
    } finally {
        carregandoVeiculos = false;
    }
}

function nomeClientePorId(clienteId) {
    if (clienteId === null || clienteId === undefined) return "Avulso";

    const cliente = clientes.find(
        (item) => String(item.id) === String(clienteId)
    );

    return cliente ? cliente.nome : `Cliente #${clienteId}`;
}

function tipoVeiculoLegivel(tipo) {
    const tipos = {
        CARRO: "Carro",
        MOTO: "Moto",
        OUTRO: "Outro"
    };

    return tipos[tipo] || tipo || "—";
}

function renderizarVeiculos() {
    tabelaVeiculos.replaceChildren();

    const termo = pesquisaVeiculo.value.trim().toLocaleLowerCase("pt-BR");

    const filtrados = veiculos.filter((veiculo) => {
        const conteudo = [
            veiculo.id,
            veiculo.placa,
            veiculo.tipo,
            veiculo.modelo,
            veiculo.cor,
            nomeClientePorId(veiculo.cliente_id),
            veiculo.ativo
        ]
            .map((valor) => String(valor ?? ""))
            .join(" ")
            .toLocaleLowerCase("pt-BR");

        return conteudo.includes(termo);
    });

    if (filtrados.length === 0) {
        const linha = document.createElement("tr");
        const celula = document.createElement("td");

        celula.colSpan = 8;
        celula.className = "empty-state";
        celula.textContent = termo
            ? "Nenhum veículo corresponde à pesquisa."
            : "Nenhum veículo cadastrado.";

        linha.appendChild(celula);
        tabelaVeiculos.appendChild(linha);
        return;
    }

    filtrados.forEach((veiculo) => {
        const linha = document.createElement("tr");

        linha.append(
            criarCelula(veiculo.id),
            criarCelula(veiculo.placa),
            criarCelula(tipoVeiculoLegivel(veiculo.tipo)),
            criarCelula(veiculo.modelo),
            criarCelula(veiculo.cor),
            criarCelula(nomeClientePorId(veiculo.cliente_id))
        );

        const celulaStatus = document.createElement("td");
        const etiqueta = document.createElement("span");
        const ativo = veiculo.ativo !== false && veiculo.ativo !== 0;

        etiqueta.className = ativo
            ? "status-badge status-active"
            : "status-badge status-inactive";

        etiqueta.textContent = ativo ? "Ativo" : "Inativo";
        celulaStatus.appendChild(etiqueta);
        linha.appendChild(celulaStatus);

        const celulaAcoes = document.createElement("td");
        const grupo = document.createElement("div");
        grupo.className = "table-actions";

        const editar = document.createElement("button");
        editar.type = "button";
        editar.className = "btn-small";
        editar.textContent = "Editar";
        editar.addEventListener("click", () => editarVeiculo(veiculo));

        const excluir = document.createElement("button");
        excluir.type = "button";
        excluir.className = "btn-small danger";
        excluir.textContent = "Excluir";
        excluir.addEventListener("click", () => excluirVeiculo(veiculo));

        grupo.append(editar, excluir);
        celulaAcoes.appendChild(grupo);
        linha.appendChild(celulaAcoes);

        tabelaVeiculos.appendChild(linha);
    });
}

function atualizarModoFormularioVeiculo(editando) {
    document.getElementById("titulo-form-veiculo").textContent =
        editando ? "Editar veículo" : "Cadastrar veículo";

    botaoSalvarVeiculo.textContent =
        editando ? "Salvar alterações" : "Cadastrar veículo";

    botaoCancelarVeiculo.hidden = !editando;
}

function limparFormularioVeiculo() {
    formVeiculo.reset();
    campoVeiculoId.value = "";
    campoVeiculoTipo.value = "CARRO";

    atualizarModoFormularioVeiculo(false);
    mostrarMensagem(mensagemVeiculo, "");
}

function editarVeiculo(veiculo) {
    campoVeiculoId.value = veiculo.id ?? "";
    campoVeiculoPlaca.value = veiculo.placa ?? "";
    campoVeiculoTipo.value = veiculo.tipo ?? "CARRO";
    campoVeiculoModelo.value = veiculo.modelo ?? "";
    campoVeiculoCor.value = veiculo.cor ?? "";
    campoVeiculoCliente.value =
        veiculo.cliente_id == null ? "" : String(veiculo.cliente_id);

    atualizarModoFormularioVeiculo(true);

    mostrarMensagem(
        mensagemVeiculo,
        `Editando o veículo ${veiculo.placa || ""}.`,
        "info"
    );

    navegarPara("veiculos");
    campoVeiculoPlaca.focus();

    formVeiculo.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });
}

function obterDadosFormularioVeiculo() {
    const placaOriginal = campoVeiculoPlaca.value.trim().toUpperCase();
    const placa = placaOriginal.replace(/[^A-Z0-9]/g, "");
    const tipo = campoVeiculoTipo.value;
    const modelo = campoVeiculoModelo.value.trim();
    const cor = campoVeiculoCor.value.trim();
    const clienteId = campoVeiculoCliente.value;

    if (!placa) {
        throw new Error("Informe a placa do veículo.");
    }

    if (!/^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$/.test(placa)) {
        throw new Error("Informe uma placa válida, com 7 caracteres (ex.: ABC1D23).");
    }

    return {
        placa,
        tipo,
        modelo: modelo || null,
        cor: cor || null,
        cliente_id: clienteId ? Number(clienteId) : null
    };
}

async function salvarVeiculo(evento) {
    evento.preventDefault();

    let dados;

    try {
        dados = obterDadosFormularioVeiculo();
    } catch (erro) {
        mostrarMensagem(mensagemVeiculo, erro.message, "error");
        return;
    }

    const id = campoVeiculoId.value.trim();
    const editando = Boolean(id);

    botaoSalvarVeiculo.disabled = true;
    botaoSalvarVeiculo.textContent = editando ? "Salvando..." : "Cadastrando...";
    mostrarMensagem(mensagemVeiculo, "");

    try {
        await requisicaoAPI(
            editando ? `/veiculos/${encodeURIComponent(id)}` : "/veiculos/",
            {
                method: editando ? "PATCH" : "POST",
                body: JSON.stringify(dados)
            }
        );

        limparFormularioVeiculo();

        mostrarMensagem(
            mensagemVeiculo,
            editando
                ? "Veículo atualizado com sucesso."
                : "Veículo cadastrado com sucesso.",
            "success"
        );

        await carregarVeiculos();
    } catch (erro) {
        if (erro.message !== "Sessão inválida.") {
            mostrarMensagem(mensagemVeiculo, erro.message, "error");
        }
    } finally {
        botaoSalvarVeiculo.disabled = false;
        botaoSalvarVeiculo.textContent = campoVeiculoId.value
            ? "Salvar alterações"
            : "Cadastrar veículo";
    }
}

async function excluirVeiculo(veiculo) {
    if (veiculo.id === undefined || veiculo.id === null) {
        mostrarMensagem(
            mensagemListaVeiculos,
            "Não foi possível identificar o ID deste veículo.",
            "error"
        );
        return;
    }

    if (!window.confirm(`Deseja realmente excluir o veículo "${veiculo.placa}"?`)) {
        return;
    }

    mostrarMensagem(mensagemListaVeiculos, "Excluindo veículo...", "info");

    try {
        await requisicaoAPI(
            `/veiculos/${encodeURIComponent(veiculo.id)}`,
            { method: "DELETE" }
        );

        if (String(campoVeiculoId.value) === String(veiculo.id)) {
            limparFormularioVeiculo();
        }

        mostrarMensagem(
            mensagemListaVeiculos,
            "Veículo excluído com sucesso.",
            "success"
        );

        await carregarVeiculos();
    } catch (erro) {
        if (erro.message !== "Sessão inválida.") {
            mostrarMensagem(mensagemListaVeiculos, erro.message, "error");
        }
    }
}

// =========================
// EVENTOS
// =========================

// Autenticação.
formLogin.addEventListener("submit", fazerLogin);

botaoLogout.addEventListener("click", () => {
    encerrarSessao("Você saiu do sistema.");
    campoSenha.value = "";
});

// Clientes.
formCliente.addEventListener("submit", salvarCliente);
botaoCancelarEdicao.addEventListener("click", limparFormularioCliente);
botaoAtualizarClientes.addEventListener("click", carregarClientes);
pesquisaCliente.addEventListener("input", renderizarClientes);

// Veículos.
formVeiculo.addEventListener("submit", salvarVeiculo);
botaoCancelarVeiculo.addEventListener("click", limparFormularioVeiculo);

botaoAtualizarVeiculos.addEventListener("click", async () => {
    await carregarClientes();
    await carregarVeiculos();
});

pesquisaVeiculo.addEventListener("input", renderizarVeiculos);

campoVeiculoPlaca.addEventListener("input", () => {
    const inicio = campoVeiculoPlaca.selectionStart;
    campoVeiculoPlaca.value = campoVeiculoPlaca.value.toUpperCase();

    if (inicio !== null) {
        campoVeiculoPlaca.setSelectionRange(inicio, inicio);
    }
});

// Navegação lateral.
document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", (evento) => {
        evento.preventDefault();
        navegarPara(link.dataset.page);
    });
});

// Atalhos do painel inicial.
document.querySelectorAll("[data-go-page]").forEach((botao) => {
    botao.addEventListener("click", () => {
        navegarPara(botao.dataset.goPage);
    });
});

// Inicia a aplicação.
document.addEventListener("DOMContentLoaded", verificarSessaoSalva);
