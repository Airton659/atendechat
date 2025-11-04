import React, { useEffect, useState } from "react";
import {
  Button,
  makeStyles,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Grid,
  Card,
  CardContent,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TablePagination,
} from "@material-ui/core";
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Visibility,
  Refresh,
} from "@material-ui/icons";

import MainContainer from "../../components/MainContainer";
import MainHeader from "../../components/MainHeader";
import MainHeaderButtonsWrapper from "../../components/MainHeaderButtonsWrapper";
import TableRowSkeleton from "../../components/TableRowSkeleton";
import Title from "../../components/Title";
import toastError from "../../errors/toastError";
import api from "../../services/api";
import { format } from "date-fns";

const useStyles = makeStyles((theme) => ({
  mainPaper: {
    flex: 1,
    padding: theme.spacing(2),
    overflowY: "scroll",
    ...theme.scrollbarStyles,
  },
  statsCard: {
    marginBottom: theme.spacing(2),
  },
  successChip: {
    backgroundColor: "#4caf50",
    color: "white",
  },
  errorChip: {
    backgroundColor: "#f44336",
    color: "white",
  },
  filterSection: {
    marginBottom: theme.spacing(2),
  },
  viewButton: {
    padding: theme.spacing(0.5),
  },
  promptBox: {
    backgroundColor: "#f5f5f5",
    padding: theme.spacing(2),
    borderRadius: theme.spacing(1),
    marginTop: theme.spacing(2),
    fontFamily: "monospace",
    fontSize: "0.9rem",
    whiteSpace: "pre-wrap",
    maxHeight: "400px",
    overflow: "auto",
  },
}));

const AgentLogs = () => {
  const classes = useStyles();
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState({
    totalLogs: 0,
    successLogs: 0,
    failedLogs: 0,
    successRate: 0,
    avgProcessingTime: 0,
  });
  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("");
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [totalCount, setTotalCount] = useState(0);
  const [selectedLog, setSelectedLog] = useState(null);
  const [detailsOpen, setDetailsOpen] = useState(false);

  useEffect(() => {
    loadTeams();
    loadStats();
    loadLogs();
  }, []);

  useEffect(() => {
    loadLogs();
  }, [selectedTeam, selectedStatus, page, rowsPerPage]);

  const loadTeams = async () => {
    try {
      const { data } = await api.get("/teams");
      setTeams(data.teams || []);
    } catch (err) {
      toastError(err);
    }
  };

  const loadStats = async () => {
    try {
      const { data } = await api.get("/agent-logs/stats");
      setStats(data);
    } catch (err) {
      toastError(err);
    }
  };

  const loadLogs = async () => {
    setLoading(true);
    try {
      const params = {
        page: page + 1,
        limit: rowsPerPage,
      };
      if (selectedTeam) params.teamId = selectedTeam;
      if (selectedStatus !== "") params.success = selectedStatus;

      const { data } = await api.get("/agent-logs", { params });
      setLogs(data.logs || []);
      setTotalCount(data.count || 0);
    } catch (err) {
      toastError(err);
    }
    setLoading(false);
  };

  const handleViewDetails = async (logId) => {
    try {
      const { data } = await api.get(`/agent-logs/${logId}`);
      setSelectedLog(data.log);
      setDetailsOpen(true);
    } catch (err) {
      toastError(err);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleRefresh = () => {
    loadStats();
    loadLogs();
  };

  return (
    <MainContainer>
      <MainHeader>
        <Title>Logs de Execução dos Agentes</Title>
        <MainHeaderButtonsWrapper>
          <Button
            variant="contained"
            color="primary"
            onClick={handleRefresh}
            startIcon={<Refresh />}
          >
            Atualizar
          </Button>
        </MainHeaderButtonsWrapper>
      </MainHeader>

      <Paper className={classes.mainPaper} variant="outlined">
        {/* Statistics Cards */}
        <Grid container spacing={2} className={classes.statsCard}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Total de Execuções
                </Typography>
                <Typography variant="h4">{stats.totalLogs}</Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Sucesso
                </Typography>
                <Typography variant="h4" style={{ color: "#4caf50" }}>
                  {stats.successLogs}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Falhas
                </Typography>
                <Typography variant="h4" style={{ color: "#f44336" }}>
                  {stats.failedLogs}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Taxa de Sucesso
                </Typography>
                <Typography variant="h4">{stats.successRate}%</Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Filters */}
        <Grid container spacing={2} className={classes.filterSection}>
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth variant="outlined" size="small">
              <InputLabel>Filtrar por Equipe</InputLabel>
              <Select
                value={selectedTeam}
                onChange={(e) => setSelectedTeam(e.target.value)}
                label="Filtrar por Equipe"
              >
                <MenuItem value="">Todas as Equipes</MenuItem>
                {teams.map((team) => (
                  <MenuItem key={team.id} value={team.id}>
                    {team.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={4}>
            <FormControl fullWidth variant="outlined" size="small">
              <InputLabel>Filtrar por Status</InputLabel>
              <Select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                label="Filtrar por Status"
              >
                <MenuItem value="">Todos</MenuItem>
                <MenuItem value="true">Sucesso</MenuItem>
                <MenuItem value="false">Falha</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>

        {/* Logs Table */}
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Data/Hora</TableCell>
              <TableCell>Equipe</TableCell>
              <TableCell>Agente</TableCell>
              <TableCell>Mensagem</TableCell>
              <TableCell>Resposta</TableCell>
              <TableCell align="center">Tempo (s)</TableCell>
              <TableCell align="center">Status</TableCell>
              <TableCell align="center">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRowSkeleton columns={8} />
            ) : (
              <>
                {logs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>
                      {format(new Date(log.createdAt), "dd/MM/yyyy HH:mm:ss")}
                    </TableCell>
                    <TableCell>{log.team?.name || "-"}</TableCell>
                    <TableCell>{log.agent?.name || "-"}</TableCell>
                    <TableCell>
                      {log.message.length > 50
                        ? log.message.substring(0, 50) + "..."
                        : log.message}
                    </TableCell>
                    <TableCell>
                      {log.response.length > 50
                        ? log.response.substring(0, 50) + "..."
                        : log.response}
                    </TableCell>
                    <TableCell align="center">
                      {log.processingTime?.toFixed(2) || "-"}
                    </TableCell>
                    <TableCell align="center">
                      {log.success ? (
                        <Chip
                          size="small"
                          icon={<SuccessIcon />}
                          label="Sucesso"
                          className={classes.successChip}
                        />
                      ) : (
                        <Chip
                          size="small"
                          icon={<ErrorIcon />}
                          label="Falha"
                          className={classes.errorChip}
                        />
                      )}
                    </TableCell>
                    <TableCell align="center">
                      <Button
                        size="small"
                        color="primary"
                        onClick={() => handleViewDetails(log.id)}
                        className={classes.viewButton}
                      >
                        <Visibility />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </>
            )}
          </TableBody>
        </Table>

        <TablePagination
          component="div"
          count={totalCount}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          labelRowsPerPage="Linhas por página:"
          labelDisplayedRows={({ from, to, count }) =>
            `${from}-${to} de ${count}`
          }
        />
      </Paper>

      {/* Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Detalhes da Execução</DialogTitle>
        <DialogContent dividers>
          {selectedLog && (
            <Box>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Data/Hora
                  </Typography>
                  <Typography>
                    {format(
                      new Date(selectedLog.createdAt),
                      "dd/MM/yyyy HH:mm:ss"
                    )}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Equipe
                  </Typography>
                  <Typography>{selectedLog.team?.name || "-"}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Agente
                  </Typography>
                  <Typography>{selectedLog.agent?.name || "-"}</Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Tempo de Processamento
                  </Typography>
                  <Typography>
                    {selectedLog.processingTime?.toFixed(2) || "-"} segundos
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Mensagem do Cliente
                  </Typography>
                  <Typography>{selectedLog.message}</Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="textSecondary">
                    Resposta do Agente
                  </Typography>
                  <Typography>{selectedLog.response}</Typography>
                </Grid>
                {selectedLog.agentConfig && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Configuração do Agente
                    </Typography>
                    <Box className={classes.promptBox}>
                      {JSON.stringify(selectedLog.agentConfig, null, 2)}
                    </Box>
                  </Grid>
                )}
                {selectedLog.teamConfig && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Configuração da Equipe
                    </Typography>
                    <Box className={classes.promptBox}>
                      {JSON.stringify(selectedLog.teamConfig, null, 2)}
                    </Box>
                  </Grid>
                )}
                {selectedLog.promptUsed && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle2" color="textSecondary">
                      Prompt Completo Enviado à IA
                    </Typography>
                    <Box className={classes.promptBox}>
                      {selectedLog.promptUsed}
                    </Box>
                  </Grid>
                )}
                {!selectedLog.success && selectedLog.errorMessage && (
                  <Grid item xs={12}>
                    <Typography
                      variant="subtitle2"
                      color="error"
                      gutterBottom
                    >
                      Mensagem de Erro
                    </Typography>
                    <Typography color="error">
                      {selectedLog.errorMessage}
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)} color="primary">
            Fechar
          </Button>
        </DialogActions>
      </Dialog>
    </MainContainer>
  );
};

export default AgentLogs;
