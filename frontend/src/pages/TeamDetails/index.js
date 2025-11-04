import React, { useEffect, useState, useReducer } from "react";
import { useParams, useHistory } from "react-router-dom";

import {
  Button,
  IconButton,
  makeStyles,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
  Grid,
  Typography,
  Card,
  CardContent,
  TextField,
  Box,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Switch,
  FormControlLabel,
} from "@material-ui/core";

import {
  ArrowBack,
  Edit,
  DeleteOutline,
  Add as AddIcon,
  Check as CheckIcon,
  Close as CloseIcon,
} from "@material-ui/icons";

import MainContainer from "../../components/MainContainer";
import MainHeader from "../../components/MainHeader";
import MainHeaderButtonsWrapper from "../../components/MainHeaderButtonsWrapper";
import TableRowSkeleton from "../../components/TableRowSkeleton";
import Title from "../../components/Title";
import toastError from "../../errors/toastError";
import api from "../../services/api";
import AgentModal from "../../components/AgentModal";
import { toast } from "react-toastify";
import ConfirmationModal from "../../components/ConfirmationModal";
import KnowledgeBaseTab from "../../components/KnowledgeBaseTab";

const useStyles = makeStyles((theme) => ({
  mainPaper: {
    flex: 1,
    padding: theme.spacing(2),
    overflowY: "scroll",
    ...theme.scrollbarStyles,
  },
  teamInfo: {
    marginBottom: theme.spacing(3),
  },
  infoCard: {
    padding: theme.spacing(2),
    marginBottom: theme.spacing(2),
  },
}));

const reducer = (state, action) => {
  console.log("[Reducer] Action:", action.type, "Payload:", action.payload);
  console.log("[Reducer] Estado anterior:", state);

  if (action.type === "LOAD_AGENTS") {
    console.log("[Reducer] LOAD_AGENTS - Retornando:", action.payload);
    return action.payload;
  }

  if (action.type === "UPDATE_AGENT") {
    const agent = action.payload;
    const agentIndex = state.findIndex((a) => a.id === agent.id);

    if (agentIndex !== -1) {
      state[agentIndex] = agent;
      return [...state];
    } else {
      return [agent, ...state];
    }
  }

  if (action.type === "DELETE_AGENT") {
    const agentId = action.payload;
    return state.filter((a) => a.id !== agentId);
  }

  if (action.type === "RESET") {
    return [];
  }

  console.log("[Reducer] Nenhuma ação correspondente, retornando state");
  return state;
};

const TeamDetails = () => {
  const classes = useStyles();
  const { teamId } = useParams();
  const history = useHistory();

  const [team, setTeam] = useState(null);
  const [agents, dispatch] = useReducer(reducer, []);
  const [loading, setLoading] = useState(false);

  const [agentModalOpen, setAgentModalOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [editingTeamName, setEditingTeamName] = useState(false);
  const [teamName, setTeamName] = useState("");

  // Estados para configurações avançadas CrewAI
  const [processType, setProcessType] = useState("sequential");
  const [managerLLM, setManagerLLM] = useState("");
  const [temperature, setTemperature] = useState(0.7);
  const [verbose, setVerbose] = useState(true);
  const [managerAgentId, setManagerAgentId] = useState(null);

  useEffect(() => {
    loadTeamData();
  }, [teamId]);

  const loadTeamData = async () => {
    setLoading(true);
    try {
      console.log("[TeamDetails] Carregando dados da equipe:", teamId);
      const response = await api.get(`/teams/${teamId}`);
      console.log("[TeamDetails] Resposta completa:", response.data);
      const { team } = response.data;

      if (!team) {
        console.error("[TeamDetails] Team não encontrado na resposta");
        throw new Error("Team data is empty");
      }

      console.log("[TeamDetails] Team carregado:", team);
      console.log("[TeamDetails] Agentes encontrados:", team.agents);
      console.log("[TeamDetails] Quantidade de agentes:", team.agents?.length);

      setTeam(team);
      setTeamName(team.name);

      // Carregar configurações avançadas
      setProcessType(team.processType || "sequential");
      setManagerLLM(team.managerLLM || "");
      setTemperature(team.temperature !== undefined ? team.temperature : 0.7);
      setVerbose(team.verbose !== undefined ? team.verbose : true);
      setManagerAgentId(team.managerAgentId || null);

      dispatch({ type: "LOAD_AGENTS", payload: team.agents || [] });
      setLoading(false);
    } catch (err) {
      console.error("[TeamDetails] Erro ao carregar team:", err);
      toastError(err);
      setLoading(false);
      history.push("/agents");
    }
  };

  const handleOpenAgentModal = () => {
    setAgentModalOpen(true);
    setSelectedAgent(null);
  };

  const handleCloseAgentModal = () => {
    setAgentModalOpen(false);
    setSelectedAgent(null);
    loadTeamData();
  };

  const handleEditAgent = (agent) => {
    setSelectedAgent(agent);
    setAgentModalOpen(true);
  };

  const handleCloseConfirmationModal = () => {
    setConfirmModalOpen(false);
    setSelectedAgent(null);
  };

  const handleDeleteAgent = async (agentId) => {
    try {
      await api.delete(`/agents/${agentId}`);
      toast.success("Agente deletado com sucesso!");
      dispatch({ type: "DELETE_AGENT", payload: agentId });
    } catch (err) {
      toastError(err);
    }
    setConfirmModalOpen(false);
    setSelectedAgent(null);
  };

  const handleSaveTeamName = async () => {
    try {
      await api.put(`/teams/${teamId}`, {
        name: teamName,
        description: team.description,
        industry: team.industry,
        isActive: team.isActive
      });
      toast.success("Nome da equipe atualizado!");
      setTeam({ ...team, name: teamName });
      setEditingTeamName(false);
    } catch (err) {
      toastError(err);
    }
  };

  const handleCancelEditTeamName = () => {
    setTeamName(team.name);
    setEditingTeamName(false);
  };

  const handleSaveAdvancedConfig = async () => {
    try {
      await api.put(`/teams/${teamId}`, {
        name: team.name,
        description: team.description,
        industry: team.industry,
        isActive: team.isActive,
        processType,
        managerLLM,
        temperature,
        verbose,
        managerAgentId
      });
      toast.success("Configurações avançadas salvas!");
      // Recarregar dados
      loadTeamData();
    } catch (err) {
      toastError(err);
    }
  };

  return (
    <MainContainer>
      <ConfirmationModal
        title="Deletar Agente"
        open={confirmModalOpen}
        onClose={handleCloseConfirmationModal}
        onConfirm={() => handleDeleteAgent(selectedAgent.id)}
      >
        Tem certeza que deseja deletar este agente?
      </ConfirmationModal>
      <AgentModal
        open={agentModalOpen}
        onClose={handleCloseAgentModal}
        agentId={selectedAgent?.id}
        teamId={teamId}
      />
      <MainHeader>
        <Title>
          <IconButton
            onClick={() => history.push("/agents")}
            style={{ marginRight: 8 }}
          >
            <ArrowBack />
          </IconButton>
          {team?.name || "Equipe"}
        </Title>
        <MainHeaderButtonsWrapper>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={handleOpenAgentModal}
          >
            Adicionar Agente
          </Button>
        </MainHeaderButtonsWrapper>
      </MainHeader>
      <Paper className={classes.mainPaper} variant="outlined">
        {team && (
          <Grid container spacing={2} className={classes.teamInfo}>
            <Grid item xs={12} md={6}>
              <Card className={classes.infoCard}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Informações da Equipe
                  </Typography>
                  <Box display="flex" alignItems="center" marginBottom={1}>
                    <Typography variant="body2" color="textSecondary" style={{ marginRight: 8 }}>
                      <strong>Nome:</strong>
                    </Typography>
                    {editingTeamName ? (
                      <>
                        <TextField
                          value={teamName}
                          onChange={(e) => setTeamName(e.target.value)}
                          size="small"
                          variant="outlined"
                          style={{ marginRight: 8 }}
                        />
                        <IconButton size="small" color="primary" onClick={handleSaveTeamName}>
                          <CheckIcon />
                        </IconButton>
                        <IconButton size="small" onClick={handleCancelEditTeamName}>
                          <CloseIcon />
                        </IconButton>
                      </>
                    ) : (
                      <>
                        <Typography variant="body2" color="textSecondary">
                          {team.name}
                        </Typography>
                        <IconButton size="small" onClick={() => setEditingTeamName(true)}>
                          <Edit fontSize="small" />
                        </IconButton>
                      </>
                    )}
                  </Box>
                  <Typography variant="body2" color="textSecondary">
                    <strong>Descrição:</strong> {team.description || "-"}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    <strong>Indústria:</strong> {team.industry || "Geral"}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    <strong>Status:</strong>{" "}
                    <Chip
                      label={team.isActive ? "Ativo" : "Inativo"}
                      color={team.isActive ? "primary" : "default"}
                      size="small"
                    />
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    <strong>Criação:</strong>{" "}
                    <Chip
                      label={team.generatedBy === "architect" ? "IA" : "Manual"}
                      color={team.generatedBy === "architect" ? "secondary" : "default"}
                      size="small"
                    />
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={6}>
              <Card className={classes.infoCard}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Estatísticas
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    <strong>Total de Agentes:</strong> {agents.length}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    <strong>Agentes Ativos:</strong>{" "}
                    {agents.filter((a) => a.isActive).length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card className={classes.infoCard}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    ⚙️ Configurações Avançadas do CrewAI
                  </Typography>

                  <Grid container spacing={2} style={{ marginTop: 8 }}>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth variant="outlined" size="small">
                        <InputLabel>Tipo de Processo</InputLabel>
                        <Select
                          value={processType}
                          onChange={(e) => setProcessType(e.target.value)}
                          label="Tipo de Processo"
                        >
                          <MenuItem value="sequential">
                            Sequential (Sequencial - um por vez)
                          </MenuItem>
                          <MenuItem value="hierarchical">
                            Hierarchical (Hierárquico - com manager)
                          </MenuItem>
                        </Select>
                      </FormControl>
                      <Typography
                        variant="caption"
                        color="textSecondary"
                        style={{ marginTop: 4, display: "block" }}
                      >
                        Sequential: agentes executam tarefas em sequência.
                        Hierarchical: um agente manager coordena os outros.
                      </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="Manager LLM (Opcional - Hierárquico)"
                        variant="outlined"
                        size="small"
                        value={managerLLM}
                        onChange={(e) => setManagerLLM(e.target.value)}
                        placeholder="gemini-2.0-flash-lite (padrão)"
                        disabled={processType !== "hierarchical"}
                        helperText={
                          processType === "hierarchical"
                            ? "Deixe vazio para usar o modelo padrão (gemini-2.0-flash-lite)"
                            : "Disponível apenas no modo Hierarchical"
                        }
                      />
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth variant="outlined" size="small">
                        <InputLabel>Agente Manager (Hierárquico)</InputLabel>
                        <Select
                          value={managerAgentId || ""}
                          onChange={(e) => setManagerAgentId(e.target.value || null)}
                          label="Agente Manager (Hierárquico)"
                          disabled={processType !== "hierarchical"}
                        >
                          <MenuItem value="">
                            <em>Nenhum (automático)</em>
                          </MenuItem>
                          {agents.map((agent) => (
                            <MenuItem key={agent.id} value={agent.id}>
                              {agent.name}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <Typography
                        variant="caption"
                        color="textSecondary"
                        style={{ marginTop: 4, display: "block" }}
                      >
                        {processType === "hierarchical"
                          ? "Agente que coordenará os demais (deixe vazio para automático)"
                          : "Disponível apenas no modo Hierarchical"}
                      </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <Typography gutterBottom>
                        Temperature: {temperature}
                      </Typography>
                      <Slider
                        value={temperature}
                        onChange={(e, newValue) => setTemperature(newValue)}
                        aria-labelledby="temperature-slider"
                        step={0.1}
                        marks
                        min={0}
                        max={2}
                        valueLabelDisplay="auto"
                      />
                      <Typography variant="caption" color="textSecondary">
                        Controla a criatividade das respostas (0 = mais
                        determinístico, 2 = mais criativo)
                      </Typography>
                    </Grid>

                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={verbose}
                            onChange={(e) => setVerbose(e.target.checked)}
                            color="primary"
                          />
                        }
                        label="Modo Verbose (logs detalhados)"
                      />
                      <Typography
                        variant="caption"
                        color="textSecondary"
                        style={{ marginTop: 4, display: "block" }}
                      >
                        Ativa logs detalhados no processamento dos agentes
                      </Typography>
                    </Grid>

                    <Grid item xs={12}>
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={handleSaveAdvancedConfig}
                        fullWidth
                      >
                        Salvar Configurações Avançadas
                      </Button>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Knowledge Base Tab */}
        {team && <KnowledgeBaseTab teamId={teamId} />}

        <Typography variant="h6" gutterBottom style={{ marginTop: 16 }}>
          Agentes da Equipe
        </Typography>

        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell align="center">Nome</TableCell>
              <TableCell align="center">Provedor IA</TableCell>
              <TableCell align="center">Função</TableCell>
              <TableCell align="center">Keywords</TableCell>
              <TableCell align="center">Status</TableCell>
              <TableCell align="center">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <>
              {agents.map((agent) => (
                <TableRow key={agent.id}>
                  <TableCell align="center">{agent.name}</TableCell>
                  <TableCell align="center">
                    <Chip
                      label={agent.aiProvider === "openai" ? "OpenAI" : "CrewAI"}
                      color={agent.aiProvider === "openai" ? "primary" : "secondary"}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    {agent.function ? agent.function.substring(0, 50) + "..." : "-"}
                  </TableCell>
                  <TableCell align="center">
                    {agent.keywords && agent.keywords.length > 0
                      ? agent.keywords.slice(0, 3).map((kw, idx) => (
                          <Chip key={idx} label={kw} size="small" style={{ margin: 2 }} />
                        ))
                      : "-"}
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={agent.isActive ? "Ativo" : "Inativo"}
                      color={agent.isActive ? "primary" : "default"}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <IconButton size="small" onClick={() => handleEditAgent(agent)}>
                      <Edit />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSelectedAgent(agent);
                        setConfirmModalOpen(true);
                      }}
                    >
                      <DeleteOutline />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {loading && <TableRowSkeleton columns={6} />}
              {!loading && agents.length === 0 && (
                <TableRow>
                  <TableCell colSpan={6} align="center">
                    <Typography variant="body2" color="textSecondary">
                      Nenhum agente cadastrado nesta equipe
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </>
          </TableBody>
        </Table>
      </Paper>
    </MainContainer>
  );
};

export default TeamDetails;
