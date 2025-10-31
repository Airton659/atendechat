import React, { useEffect, useReducer, useState } from "react";

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
  Typography,
  Chip,
} from "@material-ui/core";

import MainContainer from "../../components/MainContainer";
import MainHeader from "../../components/MainHeader";
import MainHeaderButtonsWrapper from "../../components/MainHeaderButtonsWrapper";
import TableRowSkeleton from "../../components/TableRowSkeleton";
import Title from "../../components/Title";
import toastError from "../../errors/toastError";
import api from "../../services/api";
import { DeleteOutline, Edit } from "@material-ui/icons";
import AgentModal from "../../components/AgentModal";
import { toast } from "react-toastify";
import ConfirmationModal from "../../components/ConfirmationModal";

const useStyles = makeStyles((theme) => ({
  mainPaper: {
    flex: 1,
    padding: theme.spacing(1),
    overflowY: "scroll",
    ...theme.scrollbarStyles,
  },
  customTableCell: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
}));

const reducer = (state, action) => {
  if (action.type === "LOAD_AGENTS") {
    const agents = action.payload;
    const newAgents = [];

    agents.forEach((agent) => {
      const agentIndex = state.findIndex((a) => a.id === agent.id);
      if (agentIndex !== -1) {
        state[agentIndex] = agent;
      } else {
        newAgents.push(agent);
      }
    });

    return [...state, ...newAgents];
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
    const agentIndex = state.findIndex((a) => a.id === agentId);
    if (agentIndex !== -1) {
      state.splice(agentIndex, 1);
    }
    return [...state];
  }

  if (action.type === "RESET") {
    return [];
  }
};

const Agents = () => {
  const classes = useStyles();

  const [agents, dispatch] = useReducer(reducer, []);
  const [loading, setLoading] = useState(false);

  const [agentModalOpen, setAgentModalOpen] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const { data } = await api.get("/agents");
        dispatch({ type: "LOAD_AGENTS", payload: data.agents });
        setLoading(false);
      } catch (err) {
        toastError(err);
        setLoading(false);
      }
    })();
  }, []);

  const handleOpenAgentModal = () => {
    setAgentModalOpen(true);
    setSelectedAgent(null);
  };

  const handleCloseAgentModal = () => {
    setAgentModalOpen(false);
    setSelectedAgent(null);
    // Recarregar lista
    (async () => {
      try {
        const { data } = await api.get("/agents");
        dispatch({ type: "LOAD_AGENTS", payload: data.agents });
      } catch (err) {
        toastError(err);
      }
    })();
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
      />
      <MainHeader>
        <Title>Agentes IA</Title>
        <MainHeaderButtonsWrapper>
          <Button variant="contained" color="primary" onClick={handleOpenAgentModal}>
            Adicionar Agente
          </Button>
        </MainHeaderButtonsWrapper>
      </MainHeader>
      <Paper className={classes.mainPaper} variant="outlined">
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
            </>
          </TableBody>
        </Table>
      </Paper>
    </MainContainer>
  );
};

export default Agents;
