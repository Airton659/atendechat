import React, { useState, useEffect, useReducer, useContext } from "react";
import { toast } from "react-toastify";
import { makeStyles } from "@material-ui/core/styles";
import {
  Paper,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  IconButton,
  TextField,
  InputAdornment,
  Chip,
  Tooltip
} from "@material-ui/core";
import {
  Search as SearchIcon,
  DeleteOutline as DeleteOutlineIcon,
  Edit as EditIcon,
  Add as AddIcon,
  Stars as AutoAwesomeIcon,
  School as SchoolIcon
} from "@material-ui/icons";

import MainContainer from "../../components/MainContainer";
import MainHeader from "../../components/MainHeader";
import Title from "../../components/Title";
import TableRowSkeleton from "../../components/TableRowSkeleton";
import ConfirmationModal from "../../components/ConfirmationModal";
import CrewEditorModal from "../../components/CrewEditorModal";
import CrewArchitectModal from "../../components/CrewArchitectModal";
import CrewTrainingModal from "../../components/CrewTrainingModal";

import api from "../../services/api";
import { i18n } from "../../translate/i18n";
import toastError from "../../errors/toastError";
import { SocketContext } from "../../context/Socket/SocketContext";
import { isArray } from "lodash";

const reducer = (state, action) => {
  if (action.type === "LOAD_CREWS") {
    const crews = action.payload;
    const newCrews = [];

    if (isArray(crews)) {
      crews.forEach((crew) => {
        const crewIndex = state.findIndex((c) => c.id === crew.id);
        if (crewIndex !== -1) {
          state[crewIndex] = crew;
        } else {
          newCrews.push(crew);
        }
      });
    }

    return [...state, ...newCrews];
  }

  if (action.type === "UPDATE_CREW") {
    const crew = action.payload;
    const crewIndex = state.findIndex((c) => c.id === crew.id);

    if (crewIndex !== -1) {
      state[crewIndex] = crew;
      return [...state];
    } else {
      return [crew, ...state];
    }
  }

  if (action.type === "DELETE_CREW") {
    const crewId = action.payload;
    const crewIndex = state.findIndex((c) => c.id === crewId);
    if (crewIndex !== -1) {
      state.splice(crewIndex, 1);
    }
    return [...state];
  }

  if (action.type === "RESET") {
    return [];
  }
};

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
  headerButtons: {
    display: "flex",
    gap: theme.spacing(1),
  },
}));

const Crews = () => {
  const classes = useStyles();

  const [loading, setLoading] = useState(false);
  const [crews, dispatch] = useReducer(reducer, []);
  const [selectedCrew, setSelectedCrew] = useState(null);
  const [crewModalOpen, setCrewModalOpen] = useState(false);
  const [architectModalOpen, setArchitectModalOpen] = useState(false);
  const [trainingModalOpen, setTrainingModalOpen] = useState(false);
  const [deletingCrew, setDeletingCrew] = useState(null);
  const [confirmModalOpen, setConfirmModalOpen] = useState(false);
  const [searchParam, setSearchParam] = useState("");

  const socketManager = useContext(SocketContext);

  useEffect(() => {
    dispatch({ type: "RESET" });
  }, []);

  useEffect(() => {
    setLoading(true);
    const delayDebounceFn = setTimeout(() => {
      const fetchCrews = async () => {
        try {
          const { data } = await api.get("/crews", {
            params: { searchParam },
          });
          dispatch({ type: "LOAD_CREWS", payload: data });
          setLoading(false);
        } catch (err) {
          toastError(err);
          setLoading(false);
        }
      };
      fetchCrews();
    }, 500);
    return () => clearTimeout(delayDebounceFn);
  }, [searchParam]);

  useEffect(() => {
    const companyId = localStorage.getItem("companyId");
    const socket = socketManager.getSocket(companyId);

    socket.on("crew", (data) => {
      if (data.action === "update" || data.action === "create") {
        dispatch({ type: "UPDATE_CREW", payload: data.crew });
      }

      if (data.action === "delete") {
        dispatch({ type: "DELETE_CREW", payload: +data.crewId });
      }
    });

    return () => {
      socket.disconnect();
    };
  }, [socketManager]);

  const handleOpenCrewModal = () => {
    setSelectedCrew(null);
    setCrewModalOpen(true);
  };

  const handleOpenArchitectModal = () => {
    setArchitectModalOpen(true);
  };

  const handleCloseCrewModal = () => {
    setSelectedCrew(null);
    setCrewModalOpen(false);
  };

  const handleCloseArchitectModal = () => {
    setArchitectModalOpen(false);
  };

  const handleEditCrew = (crew) => {
    setSelectedCrew(crew);
    setCrewModalOpen(true);
  };

  const handleTrainCrew = (crew) => {
    setSelectedCrew(crew);
    setTrainingModalOpen(true);
  };

  const handleCloseTrainingModal = () => {
    setSelectedCrew(null);
    setTrainingModalOpen(false);
  };

  const handleDeleteCrew = async (crewId) => {
    try {
      await api.delete(`/crews/${crewId}`);
      toast.success(i18n.t("crews.toasts.deleted"));
    } catch (err) {
      toastError(err);
    }
    setDeletingCrew(null);
    setSearchParam("");
  };

  const handleSearch = (event) => {
    setSearchParam(event.target.value.toLowerCase());
  };

  return (
    <MainContainer>
      <ConfirmationModal
        title={
          deletingCrew &&
          `${i18n.t("crews.confirmationModal.deleteTitle")} ${deletingCrew.name}?`
        }
        open={confirmModalOpen}
        onClose={setConfirmModalOpen}
        onConfirm={() => handleDeleteCrew(deletingCrew.id)}
      >
        {i18n.t("crews.confirmationModal.deleteMessage")}
      </ConfirmationModal>

      <CrewEditorModal
        open={crewModalOpen}
        onClose={handleCloseCrewModal}
        crewId={selectedCrew?.id}
      />

      <CrewArchitectModal
        open={architectModalOpen}
        onClose={handleCloseArchitectModal}
      />

      <CrewTrainingModal
        open={trainingModalOpen}
        onClose={handleCloseTrainingModal}
        crew={selectedCrew}
      />

      <MainHeader>
        <Title>{i18n.t("crews.title")}</Title>
        <div className={classes.headerButtons}>
          <Button
            variant="contained"
            color="secondary"
            startIcon={<AutoAwesomeIcon />}
            onClick={handleOpenArchitectModal}
          >
            {i18n.t("crews.buttons.architect")}
          </Button>
          <Button
            variant="contained"
            color="primary"
            startIcon={<AddIcon />}
            onClick={handleOpenCrewModal}
          >
            {i18n.t("crews.buttons.add")}
          </Button>
        </div>
      </MainHeader>

      <Paper className={classes.mainPaper} variant="outlined">
        <TextField
          fullWidth
          placeholder={i18n.t("crews.searchPlaceholder")}
          type="search"
          value={searchParam}
          onChange={handleSearch}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon style={{ color: "gray" }} />
              </InputAdornment>
            ),
          }}
        />
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell align="center">{i18n.t("crews.table.name")}</TableCell>
              <TableCell align="center">{i18n.t("crews.table.description")}</TableCell>
              <TableCell align="center">{i18n.t("crews.table.status")}</TableCell>
              <TableCell align="center">{i18n.t("crews.table.conversations")}</TableCell>
              <TableCell align="center">{i18n.t("crews.table.satisfaction")}</TableCell>
              <TableCell align="center">{i18n.t("crews.table.actions")}</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <>
              {crews.map((crew) => (
                <TableRow key={crew.id}>
                  <TableCell align="center">{crew.name}</TableCell>
                  <TableCell align="center">{crew.description}</TableCell>
                  <TableCell align="center">
                    <Chip
                      label={crew.isActive ? i18n.t("crews.status.active") : i18n.t("crews.status.inactive")}
                      color={crew.isActive ? "primary" : "default"}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="center">{crew.totalConversations || 0}</TableCell>
                  <TableCell align="center">
                    {crew.satisfactionRate ? `${(crew.satisfactionRate * 100).toFixed(1)}%` : "-"}
                  </TableCell>
                  <TableCell align="center">
                    <Tooltip title={i18n.t("crews.buttons.train")}>
                      <IconButton size="small" onClick={() => handleTrainCrew(crew)}>
                        <SchoolIcon />
                      </IconButton>
                    </Tooltip>
                    <IconButton size="small" onClick={() => handleEditCrew(crew)}>
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setDeletingCrew(crew);
                        setConfirmModalOpen(true);
                      }}
                    >
                      <DeleteOutlineIcon />
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

export default Crews;
