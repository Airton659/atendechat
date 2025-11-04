import React, { useEffect, useReducer, useState } from "react";
import { useHistory } from "react-router-dom";
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
} from "@material-ui/core";

import MainContainer from "../../components/MainContainer";
import MainHeader from "../../components/MainHeader";
import MainHeaderButtonsWrapper from "../../components/MainHeaderButtonsWrapper";
import TableRowSkeleton from "../../components/TableRowSkeleton";
import Title from "../../components/Title";
import toastError from "../../errors/toastError";
import api from "../../services/api";
import { DeleteOutline, Edit, Add as AddIcon, Stars as AutoAwesomeIcon, Visibility } from "@material-ui/icons";
import TeamArchitectModal from "../../components/TeamArchitectModal";
import { toast } from "react-toastify";
import ConfirmationModal from "../../components/ConfirmationModal";

const useStyles = makeStyles((theme) => ({
  mainPaper: {
    flex: 1,
    padding: theme.spacing(1),
    overflowY: "scroll",
    ...theme.scrollbarStyles,
  },
}));

const reducer = (state, action) => {
  if (action.type === "LOAD_TEAMS") {
    const teams = action.payload;
    return teams;
  }

  if (action.type === "UPDATE_TEAM") {
    const team = action.payload;
    const teamIndex = state.findIndex((t) => t.id === team.id);

    if (teamIndex !== -1) {
      state[teamIndex] = team;
      return [...state];
    } else {
      return [team, ...state];
    }
  }

  if (action.type === "DELETE_TEAM") {
    const teamId = action.payload;
    const teamIndex = state.findIndex((t) => t.id === teamId);
    if (teamIndex !== -1) {
      state.splice(teamIndex, 1);
    }
    return [...state];
  }

  if (action.type === "RESET") {
    return [];
  }

  return state;
};

const Teams = () => {
  const classes = useStyles();
  const history = useHistory();

  const [teams, dispatch] = useReducer(reducer, []);
  const [loading, setLoading] = useState(false);

  const [architectModalOpen, setArchitectModalOpen] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const { data } = await api.get("/teams");
        dispatch({ type: "LOAD_TEAMS", payload: data.teams });
        setLoading(false);
      } catch (err) {
        toastError(err);
        setLoading(false);
      }
    })();
  }, []);

  const handleOpenArchitectModal = () => {
    setArchitectModalOpen(true);
  };

  const handleCloseArchitectModal = () => {
    setArchitectModalOpen(false);
    // Recarregar lista
    (async () => {
      try {
        const { data } = await api.get("/teams");
        dispatch({ type: "RESET" });
        dispatch({ type: "LOAD_TEAMS", payload: data.teams });
      } catch (err) {
        toastError(err);
      }
    })();
  };

  const handleViewTeam = (team) => {
    history.push(`/teams/${team.id}`);
  };

  const handleCloseConfirmationModal = () => {
    setConfirmModalOpen(false);
    setSelectedTeam(null);
  };

  const handleDeleteTeam = async (teamId) => {
    try {
      await api.delete(`/teams/${teamId}`);
      toast.success("Equipe deletada com sucesso!");
      dispatch({ type: "DELETE_TEAM", payload: teamId });
    } catch (err) {
      toastError(err);
    }
    setConfirmModalOpen(false);
    setSelectedTeam(null);
  };

  return (
    <MainContainer>
      <ConfirmationModal
        title="Deletar Equipe"
        open={confirmModalOpen}
        onClose={handleCloseConfirmationModal}
        onConfirm={() => handleDeleteTeam(selectedTeam.id)}
      >
        Tem certeza que deseja deletar esta equipe? Todos os agentes serão removidos também.
      </ConfirmationModal>

      <TeamArchitectModal
        open={architectModalOpen}
        onClose={handleCloseArchitectModal}
        onSave={handleCloseArchitectModal}
      />

      <MainHeader>
        <Title>Equipes de Agentes IA</Title>
        <MainHeaderButtonsWrapper>
          <Button
            variant="contained"
            color="secondary"
            startIcon={<AutoAwesomeIcon />}
            onClick={handleOpenArchitectModal}
            style={{ marginRight: 8 }}
          >
            Gerar com IA
          </Button>
        </MainHeaderButtonsWrapper>
      </MainHeader>

      <Paper className={classes.mainPaper} variant="outlined">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell align="center">Nome</TableCell>
              <TableCell align="center">Descrição</TableCell>
              <TableCell align="center">Indústria</TableCell>
              <TableCell align="center">Agentes</TableCell>
              <TableCell align="center">Status</TableCell>
              <TableCell align="center">Criação</TableCell>
              <TableCell align="center">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <>
              {teams.map((team) => (
                <TableRow key={team.id}>
                  <TableCell align="center">{team.name}</TableCell>
                  <TableCell align="center">
                    {team.description ? team.description.substring(0, 50) + "..." : "-"}
                  </TableCell>
                  <TableCell align="center">
                    <Chip label={team.industry || "Geral"} size="small" />
                  </TableCell>
                  <TableCell align="center">{team.agents?.length || 0}</TableCell>
                  <TableCell align="center">
                    <Chip
                      label={team.isActive ? "Ativa" : "Inativa"}
                      color={team.isActive ? "primary" : "default"}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={team.generatedBy === "architect" ? "IA" : "Manual"}
                      color={team.generatedBy === "architect" ? "secondary" : "default"}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">
                    <IconButton size="small" onClick={() => handleViewTeam(team)} title="Ver/Editar Agentes">
                      <Visibility />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setSelectedTeam(team);
                        setConfirmModalOpen(true);
                      }}
                    >
                      <DeleteOutline />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
              {loading && <TableRowSkeleton columns={7} />}
            </>
          </TableBody>
        </Table>
      </Paper>
    </MainContainer>
  );
};

export default Teams;
