import React, { useState } from "react";
import {
  Box,
  Button,
  CircularProgress,
  TextField,
  Typography,
  Slider
} from "@material-ui/core";
import {
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  Edit as EditIcon
} from "@material-ui/icons";
import api from "../services/api";
import toastError from "../errors/toastError";
import { toast } from "react-toastify";

const FeedbackPanel = ({ result, testTask, selectedTeamId }) => {
  const [feedbackMode, setFeedbackMode] = useState(null);
  const [editedResponse, setEditedResponse] = useState("");
  const [feedbackNotes, setFeedbackNotes] = useState("");
  const [priority, setPriority] = useState(5);
  const [isSavingFeedback, setIsSavingFeedback] = useState(false);

  const handleSaveFeedback = async (feedbackType) => {
    console.log("🔍 DEBUG FeedbackPanel - result completo:", result);
    console.log("🔍 DEBUG FeedbackPanel - result.agent_id:", result?.agent_id);
    console.log("🔍 DEBUG FeedbackPanel - result keys:", result ? Object.keys(result) : 'result is null');

    if (!result || !result.agent_id) {
      console.error("❌ agent_id não encontrado!");
      toast.error("Informações do agente não encontradas");
      return;
    }

    setIsSavingFeedback(true);
    try {
      const payload = {
        agentId: result.agent_id,
        teamId: selectedTeamId,
        userMessage: testTask,
        agentResponse: result.final_output,
        feedbackType: feedbackType,
        feedbackNotes: feedbackNotes,
        priority: priority,
        usedInPrompt: true
      };

      if (feedbackType === "corrected") {
        if (!editedResponse || editedResponse.trim() === "") {
          toast.error("Por favor, forneça a resposta corrigida");
          setIsSavingFeedback(false);
          return;
        }
        payload.correctedResponse = editedResponse;
      }

      await api.post("/agent-training-examples", payload);
      toast.success(`Feedback salvo com prioridade ${priority}! O agente vai aprender com este exemplo.`);

      setFeedbackMode(null);
      setEditedResponse("");
      setFeedbackNotes("");
      setPriority(5);
    } catch (err) {
      toastError(err);
    } finally {
      setIsSavingFeedback(false);
    }
  };

  const handleApprove = () => {
    handleSaveFeedback("approved");
  };

  const handleCorrect = () => {
    if (feedbackMode !== 'edit') {
      setFeedbackMode('edit');
      setEditedResponse(result.final_output);
    } else {
      handleSaveFeedback("corrected");
    }
  };

  const handleReject = () => {
    handleSaveFeedback("rejected");
  };

  const getPriorityLabel = (value) => {
    if (value >= 10) return "🔴 CRÍTICO";
    if (value >= 8) return "🟠 MUITO IMPORTANTE";
    if (value >= 5) return "🟡 IMPORTANTE";
    return "🟢 REFERÊNCIA";
  };

  const getPriorityDescription = (value) => {
    if (value >= 10) return "Agente vai COPIAR EXATAMENTE esta resposta (políticas fixas, avisos legais)";
    if (value >= 8) return "Agente vai seguir MUITO DE PERTO este padrão (estrutura e tom mantidos)";
    if (value >= 5) return "Agente vai APRENDER o padrão e ADAPTAR ao contexto (RECOMENDADO)";
    return "Agente vai usar apenas como inspiração geral";
  };

  if (!result || !result.success) {
    return null;
  }

  return (
    <Box mt={2} p={2} style={{ backgroundColor: "#f9f9f9", borderRadius: 8 }}>
      <Typography variant="h6" gutterBottom>
        💡 Feedback de Treinamento
      </Typography>
      <Typography variant="body2" color="textSecondary" gutterBottom>
        Ajude o agente a aprender avaliando esta resposta
      </Typography>

      {feedbackMode !== 'edit' && (
        <Box mt={2} display="flex" gap={1} style={{ gap: 8 }}>
          <Button
            variant="outlined"
            color="primary"
            startIcon={<ThumbUpIcon />}
            onClick={handleApprove}
            disabled={isSavingFeedback}
          >
            👍 Aprovar
          </Button>
          <Button
            variant="outlined"
            style={{ borderColor: "#ff9800", color: "#ff9800" }}
            startIcon={<EditIcon />}
            onClick={handleCorrect}
            disabled={isSavingFeedback}
          >
            ✏️ Corrigir
          </Button>
          <Button
            variant="outlined"
            color="secondary"
            startIcon={<ThumbDownIcon />}
            onClick={handleReject}
            disabled={isSavingFeedback}
          >
            👎 Rejeitar
          </Button>
        </Box>
      )}

      {feedbackMode === 'edit' && (
        <Box mt={2}>
          <TextField
            label="Resposta Corrigida"
            fullWidth
            multiline
            rows={6}
            value={editedResponse}
            onChange={(e) => setEditedResponse(e.target.value)}
            placeholder="Edite a resposta do agente para como ela deveria ser..."
            variant="outlined"
            style={{ marginBottom: 16 }}
          />
          <TextField
            label="Notas (opcional)"
            fullWidth
            multiline
            rows={2}
            value={feedbackNotes}
            onChange={(e) => setFeedbackNotes(e.target.value)}
            placeholder="Por que você corrigiu? Ex: Faltou coletar o telefone do cliente"
            variant="outlined"
            style={{ marginBottom: 16 }}
          />

          <Box mt={2} mb={2}>
            <Typography gutterBottom>
              <strong>Prioridade:</strong> {priority} - {getPriorityLabel(priority)}
            </Typography>
            <Slider
              value={priority}
              onChange={(e, newValue) => setPriority(newValue)}
              min={0}
              max={10}
              step={1}
              marks={[
                { value: 0, label: '0' },
                { value: 5, label: '5' },
                { value: 10, label: '10' }
              ]}
              valueLabelDisplay="auto"
              style={{ marginBottom: 8 }}
            />
            <Typography variant="body2" color="textSecondary">
              {getPriorityDescription(priority)}
            </Typography>
            <Typography variant="caption" color="textSecondary" style={{ display: 'block', marginTop: 8 }}>
              • 10: 🔴 CRÍTICO - Agente COPIA EXATAMENTE (políticas fixas)<br/>
              • 8-9: 🟠 MUITO IMPORTANTE - Segue DE PERTO o padrão<br/>
              • 5-7: 🟡 IMPORTANTE - APRENDE e ADAPTA (RECOMENDADO para maioria)<br/>
              • 0-4: 🟢 REFERÊNCIA - Usa como inspiração geral
            </Typography>
          </Box>

          <Box display="flex" style={{ gap: 8 }}>
            <Button
              variant="contained"
              color="primary"
              onClick={handleCorrect}
              disabled={isSavingFeedback}
            >
              {isSavingFeedback ? <CircularProgress size={20} /> : "💾 Salvar Correção"}
            </Button>
            <Button
              variant="outlined"
              onClick={() => {
                setFeedbackMode(null);
                setEditedResponse("");
                setFeedbackNotes("");
                setPriority(5);
              }}
              disabled={isSavingFeedback}
            >
              ❌ Cancelar
            </Button>
          </Box>
        </Box>
      )}

      {!feedbackMode && (
        <>
          <Box mt={2} mb={2}>
            <Typography gutterBottom>
              <strong>Prioridade:</strong> {priority} - {getPriorityLabel(priority)}
            </Typography>
            <Slider
              value={priority}
              onChange={(e, newValue) => setPriority(newValue)}
              min={0}
              max={10}
              step={1}
              marks={[
                { value: 0, label: '0' },
                { value: 5, label: '5' },
                { value: 10, label: '10' }
              ]}
              valueLabelDisplay="auto"
              style={{ marginBottom: 8 }}
            />
            <Typography variant="body2" color="textSecondary">
              {getPriorityDescription(priority)}
            </Typography>
          </Box>

          <TextField
            label="Notas adicionais (opcional)"
            fullWidth
            multiline
            rows={2}
            value={feedbackNotes}
            onChange={(e) => setFeedbackNotes(e.target.value)}
            placeholder="Adicione observações sobre esta resposta..."
            variant="outlined"
          />
        </>
      )}
    </Box>
  );
};

export default FeedbackPanel;
