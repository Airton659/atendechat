import React, { useState } from "react";
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
} from "@material-ui/core";
import {
  Send as SendIcon,
  School as SchoolIcon,
  Clear as ClearIcon,
} from "@material-ui/icons";

import { i18n } from "../../translate/i18n";
import api from "../../services/api";
import toastError from "../../errors/toastError";

const useStyles = makeStyles((theme) => ({
  chatContainer: {
    display: "flex",
    flexDirection: "column",
    height: "500px",
  },
  messagesContainer: {
    flex: 1,
    overflowY: "auto",
    padding: theme.spacing(2),
    backgroundColor: theme.palette.background.default,
    ...theme.scrollbarStyles,
  },
  message: {
    marginBottom: theme.spacing(2),
    padding: theme.spacing(1.5),
    borderRadius: theme.spacing(1),
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
  inputContainer: {
    display: "flex",
    gap: theme.spacing(1),
    padding: theme.spacing(2),
    borderTop: `1px solid ${theme.palette.divider}`,
  },
  sendButton: {
    minWidth: "auto",
  },
}));

const CrewTrainingModal = ({ open, onClose, crew }) => {
  const classes = useStyles();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const handleClose = () => {
    setMessages([]);
    setInput("");
    onClose();
  };

  const handleClearChat = () => {
    setMessages([]);
  };

  const handleSend = async () => {
    if (!input.trim() || !crew) return;

    const userMessage = {
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    try {
      const { data } = await api.post(`/crews/${crew.id}/train`, {
        message: input,
        history: messages,
      });

      const assistantMessage = {
        role: "assistant",
        content: data.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
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

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      scroll="paper"
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <SchoolIcon />
            <span>
              {i18n.t("crews.training.title")} - {crew?.name}
            </span>
          </Box>
          <IconButton size="small" onClick={handleClearChat}>
            <ClearIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent dividers style={{ padding: 0 }}>
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
              messages.map((message, idx) => (
                <Paper
                  key={idx}
                  className={`${classes.message} ${
                    message.role === "user"
                      ? classes.userMessage
                      : classes.assistantMessage
                  }`}
                  elevation={1}
                >
                  <Typography variant="body2" style={{ whiteSpace: "pre-wrap" }}>
                    {message.content}
                  </Typography>
                </Paper>
              ))
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
              disabled={loading}
              multiline
              maxRows={4}
              size="small"
            />
            <Button
              variant="contained"
              color="primary"
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className={classes.sendButton}
            >
              <SendIcon />
            </Button>
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
