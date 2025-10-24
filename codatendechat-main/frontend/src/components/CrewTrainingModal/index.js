import React, { useState, useEffect, useRef } from "react";
import { makeStyles } from "@material-ui/core/styles";
import {
  Button,
  TextField,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
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
  Divider,
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
} from "@material-ui/icons";
import { toast } from "react-toastify";

import { i18n } from "../../translate/i18n";
import api from "../../services/api";
import toastError from "../../errors/toastError";

const useStyles = makeStyles((theme) => ({
  dialogPaper: {
    height: "90vh",
    maxHeight: "90vh",
  },
  mainContainer: {
    display: "flex",
    flexDirection: "column",
    height: "100%",
  },
  topSection: {
    padding: theme.spacing(2),
    borderBottom: `1px solid ${theme.palette.divider}`,
  },
  metricsSection: {
    padding: theme.spacing(2),
    backgroundColor: theme.palette.background.default,
    borderBottom: `1px solid ${theme.palette.divider}`,
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

const CrewTrainingModal = ({ open, onClose, crew }) => {
  const classes = useStyles();
  const messagesEndRef = useRef(null);

  const [selectedAgent, setSelectedAgent] = useState("");
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
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

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (open && crew) {
      // Selecionar primeiro agente ativo por padrão
      const agents = crew.agents || {};
      const activeAgents = Object.entries(agents).filter(([_, config]) => config.isActive);
      if (activeAgents.length > 0) {
        setSelectedAgent(activeAgents[0][0]);
      }
    }
  }, [open, crew]);

  const handleClose = () => {
    setMessages([]);
    setInput("");
    setEditingMessageIndex(null);
    setMetrics({
      totalMessages: 0,
      avgResponseTime: 0,
      correctionsCount: 0,
      avgConfidence: 0,
    });
    onClose();
  };

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
    setLoading(true);

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
      setLoading(false);
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

  const agents = crew?.agents || {};
  const activeAgents = Object.entries(agents).filter(([_, config]) => config.isActive);

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="lg"
      fullWidth
      scroll="paper"
      classes={{ paper: classes.dialogPaper }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <SchoolIcon />
            <span>{i18n.t("crews.training.title")} - {crew?.name}</span>
          </Box>
          <IconButton size="small" onClick={handleClearChat}>
            <ClearIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers style={{ padding: 0, display: "flex", flexDirection: "column" }}>
        <div className={classes.mainContainer}>
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

              {loading && (
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
                disabled={loading || !selectedAgent}
                multiline
                maxRows={4}
                size="small"
              />
              <Button
                variant="contained"
                color="primary"
                onClick={handleSend}
                disabled={loading || !input.trim() || !selectedAgent}
                className={classes.sendButton}
              >
                <SendIcon />
              </Button>
            </div>
          </div>
        </div>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} color="secondary" variant="outlined">
          {i18n.t("crews.buttons.close")}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CrewTrainingModal;
