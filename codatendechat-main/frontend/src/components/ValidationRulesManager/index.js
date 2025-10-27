import React, { useState, useEffect, useContext } from 'react';
import { AuthContext } from "../../context/Auth/AuthContext";
import {
  Box,
  Paper,
  Typography,
  Switch,
  FormControlLabel,
  Button,
  Card,
  CardContent,
  CardActions,
  IconButton,
  Chip,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Tooltip
} from '@material-ui/core';
import { Alert } from '@material-ui/lab';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon
} from '@material-ui/icons';
import { makeStyles } from '@material-ui/core/styles';
import { toast } from 'react-toastify';
import api from '../../services/api';
import ValidationRuleDialog from './ValidationRuleDialog';

const useStyles = makeStyles((theme) => ({
  root: {
    padding: theme.spacing(3),
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: theme.spacing(3),
  },
  systemToggle: {
    padding: theme.spacing(2),
    marginBottom: theme.spacing(2),
    backgroundColor: theme.palette.background.default,
  },
  ruleCard: {
    marginBottom: theme.spacing(2),
    border: '1px solid',
    borderColor: theme.palette.divider,
  },
  ruleCardDisabled: {
    opacity: 0.6,
  },
  ruleHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  ruleTitle: {
    fontWeight: 600,
    marginBottom: theme.spacing(1),
  },
  chipContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing(0.5),
    marginTop: theme.spacing(1),
  },
  addButton: {
    marginTop: theme.spacing(2),
  },
  emptyState: {
    textAlign: 'center',
    padding: theme.spacing(4),
    color: theme.palette.text.secondary,
  },
  strictnessChip: {
    fontWeight: 'bold',
  },
  entitySection: {
    marginTop: theme.spacing(2),
    padding: theme.spacing(2),
    backgroundColor: theme.palette.background.default,
    borderRadius: theme.shape.borderRadius,
  },
}));

const ValidationRulesManager = ({ teamId, agentId, agentName }) => {
  const classes = useStyles();
  const { user } = useContext(AuthContext);
  const tenantId = user?.companyId?.toString() || '';

  const [systemEnabled, setSystemEnabled] = useState(false);
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState(null);

  useEffect(() => {
    if (teamId && agentId) {
      loadValidationRules();
    }
  }, [teamId, agentId]);

  const loadValidationRules = async () => {
    try {
      setLoading(true);
      const { data } = await api.get('/api/v2/training/validation-rules', {
        params: { teamId, tenantId, agentId }
      });
      setSystemEnabled(data.enabled || false);
      setRules(data.rules || []);
    } catch (error) {
      console.error('Erro ao carregar regras de validação:', error);
      toast.error('Erro ao carregar regras de validação');
      setRules([]);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleSystem = async (event) => {
    const enabled = event.target.checked;

    try {
      await api.put('/api/v2/training/validation-rules/toggle', {
        teamId,
        tenantId,
        agentId,
        enabled
      });

      setSystemEnabled(enabled);
      toast.success(
        enabled
          ? 'Sistema de validação ativado'
          : 'Sistema de validação desativado'
      );
    } catch (error) {
      console.error('Erro ao alternar sistema de validação:', error);
      toast.error('Erro ao alternar sistema de validação');
    }
  };

  const handleAddRule = () => {
    setEditingRule(null);
    setDialogOpen(true);
  };

  const handleEditRule = (rule) => {
    setEditingRule(rule);
    setDialogOpen(true);
  };

  const handleDeleteRule = async (ruleId) => {
    if (!window.confirm('Tem certeza que deseja remover esta regra?')) {
      return;
    }

    try {
      await api.delete(`/api/v2/training/validation-rules/${ruleId}`, {
        data: { teamId, tenantId, agentId }
      });

      toast.success('Regra removida com sucesso');
      loadValidationRules();
    } catch (error) {
      console.error('Erro ao remover regra:', error);
      toast.error('Erro ao remover regra');
    }
  };

  const handleSaveRule = async (ruleData) => {
    try {
      if (editingRule) {
        // Atualizar regra existente
        await api.put(`/api/v2/training/validation-rules/${editingRule.id}`, {
          teamId,
          tenantId,
          agentId,
          updates: ruleData
        });
        toast.success('Regra atualizada com sucesso');
      } else {
        // Criar nova regra
        await api.post('/api/v2/training/validation-rules', {
          teamId,
          tenantId,
          agentId,
          rule: ruleData
        });
        toast.success('Regra criada com sucesso');
      }

      setDialogOpen(false);
      setEditingRule(null);
      loadValidationRules();
    } catch (error) {
      console.error('Erro ao salvar regra:', error);
      toast.error('Erro ao salvar regra');
    }
  };

  const getStrictnessColor = (strictness) => {
    switch (strictness) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStrictnessLabel = (strictness) => {
    switch (strictness) {
      case 'high':
        return 'Alta';
      case 'medium':
        return 'Média';
      case 'low':
        return 'Baixa';
      default:
        return strictness;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box className={classes.root}>
      <div className={classes.header}>
        <div>
          <Typography variant="h5" gutterBottom>
            Validações Programáticas
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Configure regras de validação automática para {agentName}
          </Typography>
        </div>
      </div>

      <Alert severity="info" style={{ marginBottom: 16 }}>
        <Typography variant="body2">
          <strong>Sistema Híbrido:</strong> Combine Validações (100% precisão) com Sugestões (90-95% precisão via IA)
          para garantir que o agente siga as regras da base de conhecimento.
        </Typography>
      </Alert>

      {/* Toggle do sistema */}
      <Paper className={classes.systemToggle}>
        <FormControlLabel
          control={
            <Switch
              checked={systemEnabled}
              onChange={handleToggleSystem}
              color="primary"
            />
          }
          label={
            <Box>
              <Typography variant="body1">
                {systemEnabled ? 'Sistema Ativado' : 'Sistema Desativado'}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                {systemEnabled
                  ? 'As validações serão executadas antes de cada resposta'
                  : 'Ative para começar a usar validações programáticas'}
              </Typography>
            </Box>
          }
        />
      </Paper>

      {/* Lista de regras */}
      {rules.length === 0 ? (
        <Paper className={classes.emptyState}>
          <WarningIcon style={{ fontSize: 64, color: '#ccc', marginBottom: 16 }} />
          <Typography variant="h6" gutterBottom>
            Nenhuma regra configurada
          </Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            Crie regras de validação para garantir que o agente consulte a base de conhecimento
            antes de responder em situações específicas.
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Exemplo: Validar se serviço está disponível no dia/horário solicitado
          </Typography>
        </Paper>
      ) : (
        rules.map((rule) => (
          <Card
            key={rule.id}
            className={`${classes.ruleCard} ${!rule.enabled ? classes.ruleCardDisabled : ''}`}
          >
            <CardContent>
              <div className={classes.ruleHeader}>
                <Box flex={1}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="h6" className={classes.ruleTitle}>
                      {rule.name}
                    </Typography>
                    {rule.enabled ? (
                      <CheckCircleIcon style={{ color: 'green', fontSize: 20 }} />
                    ) : (
                      <CancelIcon style={{ color: 'gray', fontSize: 20 }} />
                    )}
                  </Box>

                  {rule.description && (
                    <Typography variant="body2" color="textSecondary" paragraph>
                      {rule.description}
                    </Typography>
                  )}

                  <Box display="flex" gap={1} alignItems="center" mb={1}>
                    <Chip
                      label={getStrictnessLabel(rule.strictness)}
                      color={getStrictnessColor(rule.strictness)}
                      size="small"
                      className={classes.strictnessChip}
                    />
                    {rule.auto_correct && (
                      <Chip
                        label="Auto-correção"
                        color="primary"
                        size="small"
                      />
                    )}
                  </Box>

                  {/* Trigger Keywords */}
                  {rule.trigger_keywords && rule.trigger_keywords.length > 0 && (
                    <Box mt={1}>
                      <Typography variant="caption" color="textSecondary" display="block">
                        Palavras-gatilho:
                      </Typography>
                      <div className={classes.chipContainer}>
                        {rule.trigger_keywords.map((keyword, idx) => (
                          <Chip
                            key={idx}
                            label={keyword}
                            size="small"
                            variant="outlined"
                          />
                        ))}
                      </div>
                    </Box>
                  )}

                  {/* Extração de Entidades */}
                  {rule.entity_extraction && Object.keys(rule.entity_extraction).length > 0 && (
                    <Accordion style={{ marginTop: 16 }}>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography variant="body2">
                          Extração de Entidades ({Object.keys(rule.entity_extraction).length})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Grid container spacing={2}>
                          {Object.entries(rule.entity_extraction).map(([entityType, config]) => (
                            <Grid item xs={12} key={entityType}>
                              <Box className={classes.entitySection}>
                                <Typography variant="subtitle2" gutterBottom>
                                  {entityType}
                                </Typography>
                                <Typography variant="caption" color="textSecondary" display="block">
                                  Método: {config.method}
                                </Typography>
                                <Typography variant="caption" color="textSecondary" display="block">
                                  Padrão: <code>{config.pattern}</code>
                                </Typography>
                                {config.description && (
                                  <Typography variant="caption" color="textSecondary" display="block">
                                    {config.description}
                                  </Typography>
                                )}
                              </Box>
                            </Grid>
                          ))}
                        </Grid>
                      </AccordionDetails>
                    </Accordion>
                  )}
                </Box>
              </div>
            </CardContent>

            <CardActions>
              <Tooltip title="Editar regra">
                <IconButton
                  size="small"
                  onClick={() => handleEditRule(rule)}
                  color="primary"
                >
                  <EditIcon />
                </IconButton>
              </Tooltip>

              <Tooltip title="Remover regra">
                <IconButton
                  size="small"
                  onClick={() => handleDeleteRule(rule.id)}
                  color="secondary"
                >
                  <DeleteIcon />
                </IconButton>
              </Tooltip>

              <Box flexGrow={1} />

              <Typography variant="caption" color="textSecondary">
                Atualizado: {new Date(rule.updatedAt).toLocaleDateString()}
              </Typography>
            </CardActions>
          </Card>
        ))
      )}

      {/* Botão adicionar */}
      <Button
        variant="contained"
        color="primary"
        startIcon={<AddIcon />}
        onClick={handleAddRule}
        className={classes.addButton}
        fullWidth
      >
        Adicionar Nova Regra
      </Button>

      {/* Dialog de criação/edição */}
      <ValidationRuleDialog
        open={dialogOpen}
        onClose={() => {
          setDialogOpen(false);
          setEditingRule(null);
        }}
        onSave={handleSaveRule}
        rule={editingRule}
      />
    </Box>
  );
};

export default ValidationRulesManager;
