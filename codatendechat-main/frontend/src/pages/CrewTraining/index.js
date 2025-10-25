import React, { useState, useEffect, useRef } from "react";
import { useHistory, useParams } from "react-router-dom";
import { makeStyles } from "@material-ui/core/styles";
import {
  Button,
  TextField,
  CircularProgress,
  Paper,
  Typography,
  Box,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Grid,
  Card,
  CardContent,
  Collapse,
} from "@material-ui/core";
import {
  Send as SendIcon,
  School as SchoolIcon,
  Clear as ClearIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  TrendingUp as TrendingUpIcon,
  ArrowBack as ArrowBackIcon,
} from "@material-ui/icons";
import { toast } from "react-toastify";

import { i18n } from "../../translate/i18n";
import api from "../../services/api";
import toastError from "../../errors/toastError";
import MainContainer from "../../components/MainContainer";
import MainHeader from "../../components/MainHeader";
import MainHeaderButtonsWrapper from "../../components/MainHeaderButtonsWrapper";
import Title from "../../components/Title";

const useStyles = makeStyles((theme) => ({
  mainPaper: {
    flex: 1,
    padding: theme.spacing(2),
    overflowY: "scroll",
    ...theme.scrollbarStyles,
  },
  contentContainer: {
    display: "flex",
    flexDirection: "column",
    height: "calc(100vh - 150px)",
  },
  topSection: {
    padding: theme.spacing(2),
    marginBottom: theme.spacing(2),
    backgroundColor: theme.palette.background.paper,
    borderRadius: theme.spacing(1),
  },
  metricsSection: {
    padding: theme.spacing(2),
    marginBottom: theme.spacing(2),
    backgroundColor: theme.palette.background.default,
    borderRadius: theme.spacing(1),
  },
  metricsGrid: {
    marginTop: theme.spacing(1),
  },
  metricCard: {
    textAlign: "center",
    padding: theme.spacing(1.5),
    height: "100%",
  },
  metricValue: {
    fontSize: "1.5rem",
    fontWeight: "bold",
    color: theme.palette.primary.main,
  },
  metricLabel: {
    fontSize: "0.75rem",
    color: theme.palette.text.secondary,
    marginTop: theme.spacing(0.5),
  },
  chatContainer: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    minHeight: 0,
    backgroundColor: theme.palette.background.paper,
    borderRadius: theme.spacing(1),
    overflow: "hidden",
  },
  messagesContainer: {
    flex: 1,
    overflowY: "auto",
    padding: theme.spacing(2),
    backgroundColor: theme.palette.background.default,
    ...theme.scrollbarStyles,
  },
  messageWrapper: {
    marginBottom: theme.spacing(2),
  },
  message: {
    padding: theme.spacing(1.5),
    borderRadius: theme.spacing(1),
    position: "relative",
  },
  userMessage: {
    backgroundColor: theme.palette.primary.main,
    color: theme.palette.primary.contrastText,
    marginLeft: "auto",
    maxWidth: "70%",
  },
  assistantMessage: {
    backgroundColor: theme.palette.background.paper,
    marginRight: "auto",
    maxWidth: "70%",
  },
  messageActions: {
    display: "flex",
    gap: theme.spacing(1),
    marginTop: theme.spacing(1),
    justifyContent: "flex-end",
  },
  editContainer: {
    marginTop: theme.spacing(1),
    padding: theme.spacing(2),
    backgroundColor: theme.palette.background.paper,
    borderRadius: theme.spacing(1),
    border: `2px solid ${theme.palette.warning.main}`,
  },
  inputContainer: {
    display: "flex",
    gap: theme.spacing(1),
    padding: theme.spacing(2),
    borderTop: `1px solid ${theme.palette.divider}`,
    backgroundColor: theme.palette.background.paper,
  },
  sendButton: {
    minWidth: "auto",
  },
  agentChip: {
    marginLeft: theme.spacing(1),
  },
  metricsToggle: {
    cursor: "pointer",
    userSelect: "none",
  },
}));

const CrewTraining = () => {
  const classes = useStyles();
  const history = useHistory();
  const { crewId } = useParams();
  const messagesEndRef = useRef(null);

  const [crew, setCrew] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState("");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sendingMessage, setSendingMessage] = useState(false);
  const [editingMessageIndex, setEditingMessageIndex] = useState(null);
  const [editedContent, setEditedContent] = useState("");
  const [originalContent, setOriginalContent] = useState("");
  const [showMetrics, setShowMetrics] = useState(true);

  // Métricas
  const [metrics, setMetrics] = useState({
    totalMessages: 0,
    avgResponseTime: 0,
    correctionsCount: 0,
    avgConfidence: 0,
  });

  const scrollToBottom = () => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  const loadAgentMetrics = (agentId, crewData = null) => {
    const dataToUse = crewData || crew;
    if (!dataToUse || !agentId) return;

    const agents = dataToUse.agents || {};
    const agentTraining = agents[agentId]?.training || {};
    const savedMetrics = agentTraining.metrics || {};

    if (savedMetrics.totalMessages > 0) {
      setMetrics({
        totalMessages: savedMetrics.totalMessages || 0,
        avgResponseTime: savedMetrics.avgResponseTime || 0,
        correctionsCount: savedMetrics.correctionsCount || 0,
        avgConfidence: savedMetrics.avgConfidence || 0,
      });
      console.log(`✅ Métricas carregadas do agente ${agentId}:`, savedMetrics);
    } else {
      // Reset se não tiver métricas
      setMetrics({
        totalMessages: 0,
        avgResponseTime: 0,
        correctionsCount: 0,
        avgConfidence: 0,
      });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const fetchCrew = async () => {
      try {
        setLoading(true);
        const { data } = await api.get(`/crews/${crewId}`);
        setCrew(data);

        // Selecionar primeiro agente ativo por padrão
        const agents = data.agents || {};
        const activeAgents = Object.entries(agents)
          .filter(([_, config]) => config.isActive)
          .sort(([idA], [idB]) => idA.localeCompare(idB));

        if (activeAgents.length > 0) {
          const firstAgentId = activeAgents[0][0];
          setSelectedAgent(firstAgentId);
          loadAgentMetrics(firstAgentId, data);
        }
      } catch (err) {
        toastError(err);
        history.push("/crews");
      } finally {
        setLoading(false);
      }
    };

    if (crewId) {
      fetchCrew();
    }
  }, [crewId]);

  // Carregar métricas quando trocar de agente
  useEffect(() => {
    if (selectedAgent && crew) {
      loadAgentMetrics(selectedAgent);
    }
  }, [selectedAgent]);

  // Salvar métricas ao sair da página
  useEffect(() => {
    return () => {
      if (metrics.totalMessages > 0 && selectedAgent && crew) {
        api.post("/training/save-metrics", {
          teamId: crew.id,
          agentId: selectedAgent,
          metrics: {
            totalMessages: metrics.totalMessages,
            avgResponseTime: metrics.avgResponseTime,
            correctionsCount: metrics.correctionsCount,
            avgConfidence: metrics.avgConfidence,
          },
        }).catch(err => console.error("Erro ao salvar métricas:", err));
      }
    };
  }, [metrics, selectedAgent, crew]);

  const handleClearChat = () => {
    setMessages([]);
    setEditingMessageIndex(null);
    setMetrics({
      totalMessages: 0,
      avgResponseTime: 0,
      correctionsCount: 0,
      avgConfidence: 0,
    });
  };

  const updateMetrics = (newMessage) => {
    setMetrics((prev) => {
      const newTotal = prev.totalMessages + 1;
      const newAvgResponseTime = newMessage.responseTime
        ? (prev.avgResponseTime * prev.totalMessages + newMessage.responseTime) / newTotal
        : prev.avgResponseTime;
      const newAvgConfidence = newMessage.confidenceScore
        ? (prev.avgConfidence * prev.totalMessages + newMessage.confidenceScore) / newTotal
        : prev.avgConfidence;

      return {
        totalMessages: newTotal,
        avgResponseTime: newAvgResponseTime,
        correctionsCount: prev.correctionsCount,
        avgConfidence: newAvgConfidence,
      };
    });
  };

  const handleSend = async () => {
    if (!input.trim() || !crew || !selectedAgent) return;

    const userMessage = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setSendingMessage(true);

    try {
      const { data } = await api.post("/training/generate-response", {
        tenantId: localStorage.getItem("companyId"),
        teamId: crew.id,
        agentId: selectedAgent,
        message: input,
        conversationHistory: messages,
      });

      const assistantMessage = {
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
        agentUsed: data.agentUsed,
        responseTime: data.responseTime,
        confidenceScore: data.confidenceScore,
        knowledgeUsed: data.knowledgeUsed,
        metadata: data.metadata,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      updateMetrics(assistantMessage);
    } catch (err) {
      toastError(err);
    } finally {
      setSendingMessage(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleEditMessage = (index, content) => {
    setEditingMessageIndex(index);
    setOriginalContent(content);
    setEditedContent(content);
  };

  const handleCancelEdit = () => {
    setEditingMessageIndex(null);
    setEditedContent("");
    setOriginalContent("");
  };

  const handleSaveCorrection = async (index) => {
    const message = messages[index];

    if (!editedContent.trim() || editedContent === originalContent) {
      handleCancelEdit();
      return;
    }

    try {
      // Encontrar a mensagem do usuário anterior para contexto
      let userMessageContent = "";
      for (let i = index - 1; i >= 0; i--) {
        if (messages[i].role === "user") {
          userMessageContent = messages[i].content;
          break;
        }
      }

      const scenario = userMessageContent || "Interação geral";

      await api.post("/training/save-correction", {
        teamId: crew.id,
        tenantId: localStorage.getItem("companyId"),
        agentId: message.agentUsed || selectedAgent,
        scenario: scenario,
        badResponse: originalContent,
        goodResponse: editedContent,
      });

      // Atualizar a mensagem localmente
      setMessages((prev) => {
        const updated = [...prev];
        updated[index] = {
          ...updated[index],
          content: editedContent,
          wasEdited: true,
          originalContent: originalContent,
        };
        return updated;
      });

      setMetrics((prev) => ({
        ...prev,
        correctionsCount: prev.correctionsCount + 1,
      }));

      toast.success(i18n.t("crews.training.correctionSaved"));
      handleCancelEdit();
    } catch (err) {
      toastError(err);
    }
  };

  if (loading) {
    return (
      <MainContainer>
        <Box display="flex" alignItems="center" justifyContent="center" height="100%">
          <CircularProgress />
        </Box>
      </MainContainer>
    );
  }

  if (!crew) {
    return (
      <MainContainer>
        <Box display="flex" alignItems="center" justifyContent="center" height="100%">
          <Typography>Equipe não encontrada</Typography>
        </Box>
      </MainContainer>
    );
  }

  const agents = crew.agents || {};
  const activeAgents = Object.entries(agents)
    .filter(([_, config]) => config.isActive)
    .sort(([idA], [idB]) => idA.localeCompare(idB));

  return (
    <MainContainer>
      <MainHeader>
        <Title>
          <Box display="flex" alignItems="center" gap={1}>
            <IconButton
              edge="start"
              color="inherit"
              onClick={() => history.push("/crews")}
            >
              <ArrowBackIcon />
            </IconButton>
            <SchoolIcon />
            <span>{i18n.t("crews.training.title")} - {crew.name}</span>
          </Box>
        </Title>
        <MainHeaderButtonsWrapper>
          <Button
            variant="outlined"
            color="secondary"
            startIcon={<ClearIcon />}
            onClick={handleClearChat}
          >
            {i18n.t("crews.training.clearChat")}
          </Button>
        </MainHeaderButtonsWrapper>
      </MainHeader>

      <Paper className={classes.mainPaper} variant="outlined">
        <div className={classes.contentContainer}>
          {/* Seleção de Agente */}
          <div className={classes.topSection}>
            <FormControl fullWidth variant="outlined" size="small">
              <InputLabel>{i18n.t("crews.training.selectAgent")}</InputLabel>
              <Select
                value={selectedAgent}
                onChange={(e) => setSelectedAgent(e.target.value)}
                label={i18n.t("crews.training.selectAgent")}
              >
                {activeAgents.map(([agentId, agentConfig]) => (
                  <MenuItem key={agentId} value={agentId}>
                    {agentConfig.name} - {agentConfig.role}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </div>

          {/* Métricas */}
          <div className={classes.metricsSection}>
            <Box
              display="flex"
              alignItems="center"
              justifyContent="space-between"
              className={classes.metricsToggle}
              onClick={() => setShowMetrics(!showMetrics)}
            >
              <Box display="flex" alignItems="center" gap={1}>
                <TrendingUpIcon />
                <Typography variant="subtitle2">
                  {i18n.t("crews.training.metrics")}
                </Typography>
              </Box>
              {showMetrics ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            </Box>

            <Collapse in={showMetrics}>
              <Grid container spacing={2} className={classes.metricsGrid}>
                <Grid item xs={3}>
                  <Card className={classes.metricCard}>
                    <CardContent>
                      <Typography className={classes.metricValue}>
                        {metrics.totalMessages}
                      </Typography>
                      <Typography className={classes.metricLabel}>
                        {i18n.t("crews.training.totalMessages")}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={3}>
                  <Card className={classes.metricCard}>
                    <CardContent>
                      <Typography className={classes.metricValue}>
                        {metrics.avgResponseTime.toFixed(2)}s
                      </Typography>
                      <Typography className={classes.metricLabel}>
                        {i18n.t("crews.training.avgResponseTime")}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={3}>
                  <Card className={classes.metricCard}>
                    <CardContent>
                      <Typography className={classes.metricValue}>
                        {metrics.correctionsCount}
                      </Typography>
                      <Typography className={classes.metricLabel}>
                        {i18n.t("crews.training.corrections")}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                <Grid item xs={3}>
                  <Card className={classes.metricCard}>
                    <CardContent>
                      <Typography className={classes.metricValue}>
                        {(metrics.avgConfidence * 100).toFixed(0)}%
                      </Typography>
                      <Typography className={classes.metricLabel}>
                        {i18n.t("crews.training.avgConfidence")}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </Collapse>
          </div>

          {/* Chat Container */}
          <div className={classes.chatContainer}>
            <div className={classes.messagesContainer}>
              {messages.length === 0 ? (
                <Box
                  display="flex"
                  alignItems="center"
                  justifyContent="center"
                  height="100%"
                >
                  <Typography variant="body2" color="textSecondary">
                    {i18n.t("crews.training.startConversation")}
                  </Typography>
                </Box>
              ) : (
                <>
                  {messages.map((message, idx) => (
                    <div key={idx} className={classes.messageWrapper}>
                      <Paper
                        className={`${classes.message} ${
                          message.role === "user"
                            ? classes.userMessage
                            : classes.assistantMessage
                        }`}
                        elevation={1}
                      >
                        <Box display="flex" alignItems="flex-start" justifyContent="space-between">
                          <Box flex={1}>
                            <Typography variant="body2" style={{ whiteSpace: "pre-wrap" }}>
                              {message.content}
                            </Typography>
                            {message.wasEdited && (
                              <Chip
                                label={i18n.t("crews.training.edited")}
                                size="small"
                                color="secondary"
                                style={{ marginTop: 8 }}
                              />
                            )}
                          </Box>
                          {message.agentUsed && (
                            <Chip
                              label={agents[message.agentUsed]?.name || message.agentUsed}
                              size="small"
                              className={classes.agentChip}
                            />
                          )}
                        </Box>

                        {message.role === "assistant" && message.responseTime && (
                          <Typography variant="caption" color="textSecondary" display="block" style={{ marginTop: 4 }}>
                            {message.responseTime}s • {i18n.t("crews.training.confidence")}: {(message.confidenceScore * 100).toFixed(0)}%
                            {message.knowledgeUsed > 0 && ` • ${message.knowledgeUsed} ${i18n.t("crews.training.knowledgeSources")}`}
                          </Typography>
                        )}
                      </Paper>

                      {/* Botão de edição apenas para mensagens do assistente */}
                      {message.role === "assistant" && editingMessageIndex !== idx && (
                        <div className={classes.messageActions}>
                          <Button
                            size="small"
                            startIcon={<EditIcon />}
                            onClick={() => handleEditMessage(idx, message.content)}
                          >
                            {i18n.t("crews.training.rewrite")}
                          </Button>
                        </div>
                      )}

                      {/* Interface de edição */}
                      {editingMessageIndex === idx && (
                        <div className={classes.editContainer}>
                          <Typography variant="subtitle2" gutterBottom>
                            {i18n.t("crews.training.rewriteMessage")}
                          </Typography>
                          <TextField
                            fullWidth
                            multiline
                            rows={4}
                            variant="outlined"
                            value={editedContent}
                            onChange={(e) => setEditedContent(e.target.value)}
                            placeholder={i18n.t("crews.training.rewritePlaceholder")}
                            style={{ marginTop: 8, marginBottom: 8 }}
                          />
                          <Box display="flex" gap={1} justifyContent="flex-end">
                            <Button
                              size="small"
                              startIcon={<CancelIcon />}
                              onClick={handleCancelEdit}
                            >
                              {i18n.t("crews.buttons.cancel")}
                            </Button>
                            <Button
                              size="small"
                              variant="contained"
                              color="primary"
                              startIcon={<SaveIcon />}
                              onClick={() => handleSaveCorrection(idx)}
                            >
                              {i18n.t("crews.training.saveCorrection")}
                            </Button>
                          </Box>
                        </div>
                      )}
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </>
              )}

              {sendingMessage && (
                <Box display="flex" alignItems="center" gap={1} mt={2}>
                  <CircularProgress size={20} />
                  <Typography variant="body2" color="textSecondary">
                    {i18n.t("crews.training.thinking")}
                  </Typography>
                </Box>
              )}
            </div>

            <div className={classes.inputContainer}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder={i18n.t("crews.training.inputPlaceholder")}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={sendingMessage || !selectedAgent}
                multiline
                maxRows={4}
                size="small"
              />
              <Button
                variant="contained"
                color="primary"
                onClick={handleSend}
                disabled={sendingMessage || !input.trim() || !selectedAgent}
                className={classes.sendButton}
              >
                <SendIcon />
              </Button>
            </div>
          </div>
        </div>
      </Paper>
    </MainContainer>
  );
};

export default CrewTraining;
