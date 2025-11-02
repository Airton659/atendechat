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
} from "@material-ui/core";

import {
  ArrowBack,
  Edit,
  DeleteOutline,
  Add as AddIcon,
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
  if (action.type === "LOAD_AGENTS") {
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

  useEffect(() => {
    loadTeamData();
  }, [teamId]);

  const loadTeamData = async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/teams/${teamId}`);
      setTeam(data.team);
      dispatch({ type: "LOAD_AGENTS", payload: data.team.agents || [] });
      setLoading(false);
    } catch (err) {
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
                  <Typography variant="body2" color="textSecondary">
                    <strong>Nome:</strong> {team.name}
                  </Typography>
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
          </Grid>
        )}

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
