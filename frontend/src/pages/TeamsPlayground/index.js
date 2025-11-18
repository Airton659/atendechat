import React, { useState, useEffect } from "react";
import {
  Button,
  CircularProgress,
  Grid,
  makeStyles,
  Paper,
  TextField,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Tabs,
  Tab,
  Box,
  IconButton,
  Tooltip,
  FormControlLabel,
  Checkbox
} from "@material-ui/core";
import {
  ExpandMore as ExpandMoreIcon,
  PlayArrow as PlayArrowIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Info as InfoIcon,
  Delete as DeleteIcon
} from "@material-ui/icons";

import MainContainer from "../../components/MainContainer";
import MainHeader from "../../components/MainHeader";
import Title from "../../components/Title";
import api from "../../services/api";
import toastError from "../../errors/toastError";
import { toast } from "react-toastify";

import FeedbackPanel from "../../components/FeedbackPanel";
const useStyles = makeStyles((theme) => ({
  root: {
    display: "flex",
    flexDirection: "column",
    height: "calc(100vh - 100px)",
  },
  gridContainer: {
    flex: 1,
    overflow: "hidden",
  },
  column: {
    height: "100%",
    display: "flex",
    flexDirection: "column",
  },
  columnPaper: {
    flex: 1,
    padding: theme.spacing(2),
    overflowY: "auto",
    ...theme.scrollbarStyles,
  },
  columnHeader: {
    marginBottom: theme.spacing(2),
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  textField: {
    marginBottom: theme.spacing(2),
  },
  agentAccordion: {
    marginBottom: theme.spacing(1),
  },
  runButton: {
    marginTop: theme.spacing(2),
    marginBottom: theme.spacing(2),
  },
  logsContainer: {
    backgroundColor: "#1e1e1e",
    color: "#d4d4d4",
    padding: theme.spacing(2),
    borderRadius: 4,
    fontFamily: "Monaco, Courier New, monospace",
    fontSize: "12px",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    maxHeight: "500px",
    overflowY: "auto",
  },
  outputContainer: {
    backgroundColor: "#f5f5f5",
    padding: theme.spacing(2),
    borderRadius: 4,
    marginBottom: theme.spacing(2),
  },
  chipContainer: {
    display: "flex",
    gap: theme.spacing(1),
    marginTop: theme.spacing(1),
    flexWrap: "wrap",
  },
}));

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      {...other}
    >
      {value === index && <Box p={2}>{children}</Box>}
    </div>
  );
}

const TeamsPlayground = () => {
  const classes = useStyles();

  // Estado: Lista de times disponíveis
  const [teams, setTeams] = useState([]);
  const [selectedTeamId, setSelectedTeamId] = useState("");

  // Estado: Configuração do time (editável)
  const [teamConfig, setTeamConfig] = useState({
    name: "",
    description: "",
    processType: "sequential",
    temperature: 0.7,
    verbose: true,
    agents: []
  });

  // Estado: Input de teste
  const [testTask, setTestTask] = useState("");

  // Estado: Conversação contínua
  const [continuousConversation, setContinuousConversation] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);

  // Estado: Resultados
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [currentTab, setCurrentTab] = useState(0);

  // Carregar times ao montar
  useEffect(() => {
    loadTeams();
  }, []);

  const loadTeams = async () => {
    try {
      const { data } = await api.get("/teams");
      setTeams(data.teams);
    } catch (err) {
      toastError(err);
    }
  };

  // Carregar time selecionado
  const handleTeamSelect = async (teamId) => {
    setSelectedTeamId(teamId);

    if (!teamId) {
      setTeamConfig({
        name: "",
        description: "",
        processType: "sequential",
        temperature: 0.7,
        verbose: true,
        agents: []
      });
      return;
    }

    try {
      const { data } = await api.get(`/teams/${teamId}`);
      const team = data.team;

      setTeamConfig({
        id: team.id,
        name: team.name,
        description: team.description || "",
        processType: team.processType || "sequential",
        temperature: team.temperature || 0.7,
        verbose: team.verbose !== false,
        managerLLM: team.managerLLM || "",
        managerAgentId: team.managerAgentId || null,
        defaultAgentId: team.defaultAgentId || null,
        agents: team.agents.map(agent => ({
          id: agent.id,
          name: agent.name,
          function: agent.function,
          objective: agent.objective,
          backstory: agent.backstory,
          keywords: agent.keywords || [],
          customInstructions: agent.customInstructions || "",
          persona: agent.persona || "",
          doList: agent.doList || [],
          dontList: agent.dontList || [],
          isActive: agent.isActive !== false,
          useKnowledgeBase: agent.useKnowledgeBase || false,
          knowledgeBaseIds: agent.knowledgeBases?.map(kb => kb.documentId) || []
        }))
      });
    } catch (err) {
      toastError(err);
    }
  };

  // Atualizar campo do time
  const handleTeamFieldChange = (field, value) => {
    setTeamConfig(prev => ({ ...prev, [field]: value }));
  };

  // Atualizar campo de um agente
  const handleAgentFieldChange = (agentIndex, field, value) => {
    setTeamConfig(prev => {
      const newAgents = [...prev.agents];
      newAgents[agentIndex] = { ...newAgents[agentIndex], [field]: value };
      return { ...prev, agents: newAgents };
    });
  };

  // Executar teste
  const handleRunTest = async () => {
    if (!testTask.trim()) {
      toast.error("Digite uma tarefa para testar");
      return;
    }

    if (!teamConfig.agents || teamConfig.agents.length === 0) {
      toast.error("Selecione um time com pelo menos 1 agente");
      return;
    }

    setIsRunning(true);
    setResult(null);

    try {
      console.log("🧪 DEBUG - teamConfig being sent:", JSON.stringify(teamConfig, null, 2));

      const { data } = await api.post("/teams/playground/run", {
        teamDefinition: teamConfig,
        task: testTask,
        conversationHistory: continuousConversation ? conversationHistory : []
      });

      setResult(data);
      setCurrentTab(0); // Mostrar tab de resultado

      // Se conversação contínua, adicionar ao histórico
      if (continuousConversation && data.success) {
        setConversationHistory(prev => [
          ...prev,
          { role: "user", content: testTask },
          { role: "assistant", content: data.final_output }
        ]);
      }

      toast.success(`Teste concluído! Agente usado: ${data.agent_used}`);
    } catch (err) {
      toastError(err);
    } finally {
      setIsRunning(false);
    }
  };

  // Limpar histórico de conversação
  const handleClearHistory = () => {
    setConversationHistory([]);
    toast.info("Histórico de conversação limpo");
  };

  // Salvar alterações no banco
  const handleSaveChanges = async () => {
    if (!selectedTeamId) {
      toast.error("Selecione um time existente para salvar alterações");
      return;
    }

    try {
      // Atualizar o time e seus agentes
      await api.put(`/teams/${selectedTeamId}`, {
        name: teamConfig.name,
        description: teamConfig.description,
        processType: teamConfig.processType,
        managerLLM: teamConfig.managerLLM,
        temperature: teamConfig.temperature,
        verbose: teamConfig.verbose,
        managerAgentId: teamConfig.managerAgentId,
        defaultAgentId: teamConfig.defaultAgentId
      });

      // Atualizar cada agente
      for (const agent of teamConfig.agents) {
        // Garantir que arrays existem (mesmo vazios)
        const keywords = Array.isArray(agent.keywords) ? agent.keywords :
                        (typeof agent.keywords === 'string' ? agent.keywords.split(',').map(k => k.trim()).filter(k => k) : []);

        const doList = Array.isArray(agent.doList) ? agent.doList :
                      (typeof agent.doList === 'string' ? agent.doList.split('\n').filter(item => item.trim()) : []);

        const dontList = Array.isArray(agent.dontList) ? agent.dontList :
                        (typeof agent.dontList === 'string' ? agent.dontList.split('\n').filter(item => item.trim()) : []);

        await api.put(`/agents/${agent.id}`, {
          name: agent.name,
          function: agent.function,
          objective: agent.objective,
          backstory: agent.backstory,
          persona: agent.persona,
          customInstructions: agent.customInstructions,
          keywords: keywords,
          doList: doList,
          dontList: dontList,
          isActive: agent.isActive
        });
      }

      toast.success("Alterações salvas com sucesso!");

      // Recarregar o time do banco para confirmar
      const { data } = await api.get(`/teams/${selectedTeamId}`);
      const team = data.team;

      setTeamConfig({
        id: team.id,
        name: team.name,
        description: team.description || "",
        processType: team.processType || "sequential",
        temperature: team.temperature || 0.7,
        verbose: team.verbose !== false,
        managerLLM: team.managerLLM || "",
        managerAgentId: team.managerAgentId || null,
        defaultAgentId: team.defaultAgentId || null,
        agents: team.agents.map(agent => ({
          id: agent.id,
          name: agent.name,
          function: agent.function,
          objective: agent.objective,
          backstory: agent.backstory,
          keywords: agent.keywords || [],
          customInstructions: agent.customInstructions || "",
          persona: agent.persona || "",
          doList: agent.doList || [],
          dontList: agent.dontList || [],
          isActive: agent.isActive !== false,
          useKnowledgeBase: agent.useKnowledgeBase || false,
          knowledgeBaseIds: agent.knowledgeBases?.map(kb => kb.documentId) || []
        }))
      });
    } catch (err) {
      toastError(err);
    }
  };

  return (
    <MainContainer>
      <MainHeader>
        <Title>🧪 Laboratório de Times (Playground)</Title>
      </MainHeader>

      <div className={classes.root}>
        <Grid container spacing={2} className={classes.gridContainer}>
          {/* COLUNA 1: Configuração do Time */}
          <Grid item xs={12} md={4} className={classes.column}>
            <Paper className={classes.columnPaper}>
              <div className={classes.columnHeader}>
                <Typography variant="h6">⚙️ Configuração</Typography>
                <Tooltip title="Carregue um time e edite os prompts livremente">
                  <IconButton size="small">
                    <InfoIcon />
                  </IconButton>
                </Tooltip>
              </div>

              {/* Seletor de Time */}
              <FormControl fullWidth className={classes.textField}>
                <InputLabel>Carregar Time Existente</InputLabel>
                <Select
                  value={selectedTeamId}
                  onChange={(e) => handleTeamSelect(e.target.value)}
                >
                  <MenuItem value="">
                    <em>Nenhum (criar do zero)</em>
                  </MenuItem>
                  {teams.map(team => (
                    <MenuItem key={team.id} value={team.id}>
                      {team.name} ({team.agents?.length || 0} agentes)
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Campos do Time */}
              <TextField
                label="Nome do Time"
                fullWidth
                className={classes.textField}
                value={teamConfig.name}
                onChange={(e) => handleTeamFieldChange("name", e.target.value)}
              />

              <TextField
                label="Descrição"
                fullWidth
                multiline
                rows={2}
                className={classes.textField}
                value={teamConfig.description}
                onChange={(e) => handleTeamFieldChange("description", e.target.value)}
              />

              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <FormControl fullWidth className={classes.textField}>
                    <InputLabel>Processo</InputLabel>
                    <Select
                      value={teamConfig.processType}
                      onChange={(e) => handleTeamFieldChange("processType", e.target.value)}
                    >
                      <MenuItem value="sequential">Sequential</MenuItem>
                      <MenuItem value="hierarchical">Hierarchical</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={6}>
                  <TextField
                    label="Temperature"
                    type="number"
                    fullWidth
                    className={classes.textField}
                    value={teamConfig.temperature}
                    onChange={(e) => handleTeamFieldChange("temperature", parseFloat(e.target.value))}
                    inputProps={{ min: 0, max: 2, step: 0.1 }}
                  />
                </Grid>
              </Grid>

              {/* Agentes (Accordions) */}
              <Typography variant="subtitle2" style={{ marginTop: 16, marginBottom: 8 }}>
                Agentes ({teamConfig.agents.length})
              </Typography>

              {teamConfig.agents.map((agent, index) => (
                <Accordion key={index} className={classes.agentAccordion}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Typography>{agent.name}</Typography>
                    {!agent.isActive && (
                      <Chip label="Inativo" size="small" style={{ marginLeft: 8 }} />
                    )}
                  </AccordionSummary>
                  <AccordionDetails style={{ flexDirection: "column" }}>
                    {/* Toggle Ativo/Inativo */}
                    <FormControl fullWidth className={classes.textField}>
                      <Grid container alignItems="center" spacing={2}>
                        <Grid item>
                          <Typography variant="body2">Agente Inativo</Typography>
                        </Grid>
                        <Grid item>
                          <input
                            type="checkbox"
                            checked={agent.isActive}
                            onChange={(e) => handleAgentFieldChange(index, "isActive", e.target.checked)}
                            style={{ transform: "scale(1.5)" }}
                          />
                        </Grid>
                        <Grid item>
                          <Typography variant="body2">Agente Ativo</Typography>
                        </Grid>
                      </Grid>
                    </FormControl>

                    <TextField
                      label="Nome"
                      fullWidth
                      className={classes.textField}
                      value={agent.name}
                      onChange={(e) => handleAgentFieldChange(index, "name", e.target.value)}
                    />

                    <TextField
                      label="Função (Role)"
                      fullWidth
                      multiline
                      rows={2}
                      className={classes.textField}
                      value={agent.function}
                      onChange={(e) => handleAgentFieldChange(index, "function", e.target.value)}
                      helperText="Descreva o papel do agente (ex: 'Assistente de triagem')"
                    />

                    <TextField
                      label="Objetivo (Goal)"
                      fullWidth
                      multiline
                      rows={2}
                      className={classes.textField}
                      value={agent.objective}
                      onChange={(e) => handleAgentFieldChange(index, "objective", e.target.value)}
                      helperText="O que o agente deve alcançar"
                    />

                    <TextField
                      label="Backstory"
                      fullWidth
                      multiline
                      rows={3}
                      className={classes.textField}
                      value={agent.backstory}
                      onChange={(e) => handleAgentFieldChange(index, "backstory", e.target.value)}
                      helperText="História e contexto do agente"
                    />

                    <TextField
                      label="Persona"
                      fullWidth
                      multiline
                      rows={2}
                      className={classes.textField}
                      value={agent.persona}
                      onChange={(e) => handleAgentFieldChange(index, "persona", e.target.value)}
                      helperText="Personalidade e tom de voz (ex: 'Profissional e empático')"
                    />

                    <TextField
                      label="Instruções Customizadas"
                      fullWidth
                      multiline
                      rows={3}
                      className={classes.textField}
                      value={agent.customInstructions}
                      onChange={(e) => handleAgentFieldChange(index, "customInstructions", e.target.value)}
                      helperText="Instruções especiais ou regras específicas"
                    />

                    <TextField
                      label="Keywords (separadas por vírgula)"
                      fullWidth
                      className={classes.textField}
                      value={agent.keywords.join(", ")}
                      onChange={(e) => handleAgentFieldChange(index, "keywords", e.target.value.split(",").map(k => k.trim()))}
                      helperText="Palavras-chave para ativar este agente"
                    />

                    <TextField
                      label="DO List (uma por linha)"
                      fullWidth
                      multiline
                      rows={4}
                      variant="outlined"
                      className={classes.textField}
                      value={agent.doList.join("\n")}
                      onChange={(e) => handleAgentFieldChange(index, "doList", e.target.value.split("\n"))}
                      helperText="Coisas que o agente DEVE fazer (pressione Enter para nova linha)"
                      placeholder="Sempre perguntar o nome do cliente&#10;Confirmar o email antes de continuar&#10;Agradecer ao final"
                    />

                    <TextField
                      label="DON'T List (uma por linha)"
                      fullWidth
                      multiline
                      rows={4}
                      variant="outlined"
                      className={classes.textField}
                      value={agent.dontList.join("\n")}
                      onChange={(e) => handleAgentFieldChange(index, "dontList", e.target.value.split("\n"))}
                      helperText="Coisas que o agente NÃO DEVE fazer (pressione Enter para nova linha)"
                      placeholder="Nunca fornecer descontos sem autorização&#10;Não interromper o cliente&#10;Evitar linguagem técnica complexa"
                    />
                  </AccordionDetails>
                </Accordion>
              ))}
            </Paper>
          </Grid>

          {/* COLUNA 2: Teste e Execução */}
          <Grid item xs={12} md={4} className={classes.column}>
            <Paper className={classes.columnPaper}>
              <div className={classes.columnHeader}>
                <Typography variant="h6">🚀 Teste</Typography>
              </div>

              <TextField
                label="Tarefa de Teste"
                fullWidth
                multiline
                rows={6}
                className={classes.textField}
                value={testTask}
                onChange={(e) => setTestTask(e.target.value)}
                placeholder="Digite uma mensagem para testar o time..."
                helperText="Exemplo: 'Olá, preciso de ajuda com meu pedido 123'"
              />

              <FormControlLabel
                control={
                  <Checkbox
                    checked={continuousConversation}
                    onChange={(e) => {
                      setContinuousConversation(e.target.checked);
                      if (!e.target.checked) {
                        setConversationHistory([]);
                      }
                    }}
                    color="primary"
                  />
                }
                label={`Conversação Contínua ${conversationHistory.length > 0 ? `(${conversationHistory.length / 2} msgs)` : ''}`}
              />

              {continuousConversation && conversationHistory.length > 0 && (
                <Button
                  variant="outlined"
                  size="small"
                  onClick={handleClearHistory}
                  startIcon={<DeleteIcon />}
                  style={{ marginBottom: '16px' }}
                >
                  Limpar Histórico
                </Button>
              )}

              <Button
                variant="contained"
                color="primary"
                fullWidth
                size="large"
                className={classes.runButton}
                onClick={handleRunTest}
                disabled={isRunning || !teamConfig.agents.length}
                startIcon={isRunning ? <CircularProgress size={20} color="inherit" /> : <PlayArrowIcon />}
              >
                {isRunning ? "Executando..." : "Executar Teste"}
              </Button>

              {result && (
                <div className={classes.chipContainer}>
                  <Chip
                    label={`Tempo: ${result.processing_time}s`}
                    color="primary"
                    size="small"
                  />
                  <Chip
                    label={`Agente: ${result.agent_used}`}
                    color="secondary"
                    size="small"
                  />
                  <Chip
                    label={result.success ? "✅ Sucesso" : "❌ Erro"}
                    color={result.success ? "primary" : "secondary"}
                    size="small"
                  />
                </div>
              )}

              <Button
                variant="outlined"
                color="primary"
                fullWidth
                style={{ marginTop: 16 }}
                onClick={handleSaveChanges}
                disabled={!selectedTeamId}
                startIcon={<SaveIcon />}
              >
                Salvar Alterações no Banco
              </Button>

              <Button
                variant="outlined"
                fullWidth
                style={{ marginTop: 8 }}
                onClick={() => handleTeamSelect(selectedTeamId)}
                disabled={!selectedTeamId}
                startIcon={<RefreshIcon />}
              >
                Resetar para Original
              </Button>
            </Paper>
          </Grid>

          {/* COLUNA 3: Resultados */}
          <Grid item xs={12} md={4} className={classes.column}>
            <Paper className={classes.columnPaper}>
              <div className={classes.columnHeader}>
                <Typography variant="h6">📊 Resultados</Typography>
              </div>

              {!result && (
                <Typography variant="body2" color="textSecondary" align="center" style={{ marginTop: 32 }}>
                  Execute um teste para ver os resultados aqui
                </Typography>
              )}

              {result && (
                <>
                  <Tabs
                    value={currentTab}
                    onChange={(e, newValue) => setCurrentTab(newValue)}
                    indicatorColor="primary"
                    textColor="primary"
                  >
                    <Tab label="Resposta Final" />
                    <Tab label="Logs de Execução" />
                  </Tabs>

                  <TabPanel value={currentTab} index={0}>
                    <div className={classes.outputContainer}>
                      <Typography variant="body1" style={{ whiteSpace: "pre-wrap" }}>
                        {result.final_output}
                      </Typography>
                    </div>
                  </TabPanel>

                  <TabPanel value={currentTab} index={1}>
                    <div className={classes.logsContainer}>
                      {result.execution_logs || "Nenhum log disponível"}
                    </div>
                  </TabPanel>
                  <FeedbackPanel result={result} testTask={testTask} selectedTeamId={selectedTeamId} />
                </>
              )}
            </Paper>
          </Grid>
        </Grid>
      </div>
    </MainContainer>
  );
};

export default TeamsPlayground;
