import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Tabs,
  Tab,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Grid,
  Paper,
  Switch,
  FormControlLabel,
  Divider,
} from '@material-ui/core';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Close as CloseIcon,
} from '@material-ui/icons';
import { makeStyles } from '@material-ui/core/styles';

const useStyles = makeStyles((theme) => ({
  dialogContent: {
    minHeight: 400,
  },
  tabPanel: {
    paddingTop: theme.spacing(2),
  },
  chipInput: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: theme.spacing(0.5),
    marginTop: theme.spacing(1),
  },
  entityCard: {
    padding: theme.spacing(2),
    marginBottom: theme.spacing(2),
    border: '1px solid',
    borderColor: theme.palette.divider,
  },
  addEntityButton: {
    marginTop: theme.spacing(2),
  },
}));

const TabPanel = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`validation-tabpanel-${index}`}
      aria-labelledby={`validation-tab-${index}`}
      {...other}
    >
      {value === index && <Box>{children}</Box>}
    </div>
  );
};

const ValidationRuleDialog = ({ open, onClose, onSave, rule }) => {
  const classes = useStyles();
  const [activeTab, setActiveTab] = useState(0);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    trigger_keywords: [],
    entity_extraction: {},
    strictness: 'medium',
    auto_correct: false,
    enabled: true,
  });

  const [keywordInput, setKeywordInput] = useState('');
  const [newEntity, setNewEntity] = useState({
    type: '',
    method: 'keywords',
    pattern: '',
    description: '',
  });

  useEffect(() => {
    if (rule) {
      // Modo edição
      setFormData({
        name: rule.name || '',
        description: rule.description || '',
        trigger_keywords: rule.trigger_keywords || [],
        entity_extraction: rule.entity_extraction || {},
        strictness: rule.strictness || 'medium',
        auto_correct: rule.auto_correct || false,
        enabled: rule.enabled !== undefined ? rule.enabled : true,
      });
    } else {
      // Modo criação
      setFormData({
        name: '',
        description: '',
        trigger_keywords: [],
        entity_extraction: {},
        strictness: 'medium',
        auto_correct: false,
        enabled: true,
      });
    }
    setActiveTab(0);
  }, [rule, open]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleAddKeyword = () => {
    if (keywordInput.trim()) {
      setFormData((prev) => ({
        ...prev,
        trigger_keywords: [...prev.trigger_keywords, keywordInput.trim()],
      }));
      setKeywordInput('');
    }
  };

  const handleRemoveKeyword = (index) => {
    setFormData((prev) => ({
      ...prev,
      trigger_keywords: prev.trigger_keywords.filter((_, i) => i !== index),
    }));
  };

  const handleAddEntity = () => {
    if (newEntity.type.trim() && newEntity.pattern.trim()) {
      setFormData((prev) => ({
        ...prev,
        entity_extraction: {
          ...prev.entity_extraction,
          [newEntity.type]: {
            method: newEntity.method,
            pattern: newEntity.pattern,
            description: newEntity.description,
          },
        },
      }));

      // Resetar formulário de entidade
      setNewEntity({
        type: '',
        method: 'keywords',
        pattern: '',
        description: '',
      });
    }
  };

  const handleRemoveEntity = (entityType) => {
    setFormData((prev) => {
      const newExtraction = { ...prev.entity_extraction };
      delete newExtraction[entityType];
      return {
        ...prev,
        entity_extraction: newExtraction,
      };
    });
  };

  const handleSave = () => {
    // Validações básicas
    if (!formData.name.trim()) {
      alert('Nome da regra é obrigatório');
      return;
    }

    if (formData.trigger_keywords.length === 0) {
      alert('Adicione pelo menos uma palavra-gatilho');
      return;
    }

    onSave(formData);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">
            {rule ? 'Editar Regra de Validação' : 'Nova Regra de Validação'}
          </Typography>
          <IconButton size="small" onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent className={classes.dialogContent}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label="Básico" />
          <Tab label="Triggers" />
          <Tab label="Entidades" />
          <Tab label="Avançado" />
        </Tabs>

        <Box className={classes.tabPanel}>
          {/* TAB 0: BÁSICO */}
          <TabPanel value={activeTab} index={0}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Nome da Regra"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  placeholder="Ex: Validar agendamentos médicos"
                  required
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Descrição"
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  placeholder="Explique o objetivo desta regra..."
                />
              </Grid>

              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.enabled}
                      onChange={(e) => handleChange('enabled', e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Regra ativada"
                />
                <Typography variant="caption" color="textSecondary" display="block">
                  Desative temporariamente sem excluir a regra
                </Typography>
              </Grid>
            </Grid>
          </TabPanel>

          {/* TAB 1: TRIGGERS */}
          <TabPanel value={activeTab} index={1}>
            <Typography variant="body2" gutterBottom>
              Defina palavras-chave que ativam esta validação quando aparecerem na mensagem do cliente.
            </Typography>

            <Box mt={2}>
              <TextField
                fullWidth
                label="Adicionar palavra-gatilho"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleAddKeyword();
                  }
                }}
                placeholder="Ex: agendar, marcar, consulta"
                InputProps={{
                  endAdornment: (
                    <IconButton onClick={handleAddKeyword} size="small" color="primary">
                      <AddIcon />
                    </IconButton>
                  ),
                }}
              />

              <Box className={classes.chipInput}>
                {formData.trigger_keywords.map((keyword, index) => (
                  <Chip
                    key={index}
                    label={keyword}
                    onDelete={() => handleRemoveKeyword(index)}
                    color="primary"
                  />
                ))}
              </Box>

              {formData.trigger_keywords.length === 0 && (
                <Typography variant="caption" color="error" display="block" mt={1}>
                  Adicione pelo menos uma palavra-gatilho
                </Typography>
              )}
            </Box>
          </TabPanel>

          {/* TAB 2: ENTIDADES */}
          <TabPanel value={activeTab} index={2}>
            <Typography variant="body2" gutterBottom>
              Configure quais entidades devem ser extraídas da mensagem e validadas contra a base de conhecimento.
            </Typography>

            {/* Entidades existentes */}
            {Object.entries(formData.entity_extraction).length > 0 && (
              <Box mt={2} mb={3}>
                <Typography variant="subtitle2" gutterBottom>
                  Entidades Configuradas:
                </Typography>
                {Object.entries(formData.entity_extraction).map(([entityType, config]) => (
                  <Paper key={entityType} className={classes.entityCard}>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                      <Box flex={1}>
                        <Typography variant="subtitle1" gutterBottom>
                          {entityType}
                        </Typography>
                        <Typography variant="caption" color="textSecondary" display="block">
                          Método: <strong>{config.method}</strong>
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
                      <IconButton size="small" onClick={() => handleRemoveEntity(entityType)}>
                        <DeleteIcon />
                      </IconButton>
                    </Box>
                  </Paper>
                ))}
              </Box>
            )}

            <Divider style={{ margin: '16px 0' }} />

            {/* Adicionar nova entidade */}
            <Typography variant="subtitle2" gutterBottom>
              Adicionar Nova Entidade:
            </Typography>

            <Grid container spacing={2} style={{ marginTop: 8 }}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Tipo de Entidade"
                  value={newEntity.type}
                  onChange={(e) => setNewEntity({ ...newEntity, type: e.target.value })}
                  placeholder="Ex: service_type, time_period"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Método de Extração</InputLabel>
                  <Select
                    value={newEntity.method}
                    onChange={(e) => setNewEntity({ ...newEntity, method: e.target.value })}
                  >
                    <MenuItem value="keywords">Keywords (lista separada por vírgula)</MenuItem>
                    <MenuItem value="regex">Regex (expressão regular)</MenuItem>
                    <MenuItem value="line_starts">Line Starts (linhas que começam com...)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Padrão"
                  value={newEntity.pattern}
                  onChange={(e) => setNewEntity({ ...newEntity, pattern: e.target.value })}
                  placeholder={
                    newEntity.method === 'keywords'
                      ? 'Ex: segunda,terça,quarta,quinta,sexta'
                      : newEntity.method === 'regex'
                      ? 'Ex: consulta\\s+(?:de\\s+)?(\\w+)'
                      : 'Ex: Profissional:'
                  }
                  helperText={
                    newEntity.method === 'keywords'
                      ? 'Liste as opções separadas por vírgula'
                      : newEntity.method === 'regex'
                      ? 'Use expressão regular válida (JavaScript)'
                      : 'Prefixo que inicia a linha'
                  }
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Descrição (opcional)"
                  value={newEntity.description}
                  onChange={(e) => setNewEntity({ ...newEntity, description: e.target.value })}
                  placeholder="Ex: Extrai o tipo de consulta médica"
                />
              </Grid>

              <Grid item xs={12}>
                <Button
                  variant="outlined"
                  color="primary"
                  startIcon={<AddIcon />}
                  onClick={handleAddEntity}
                  disabled={!newEntity.type.trim() || !newEntity.pattern.trim()}
                  fullWidth
                >
                  Adicionar Entidade
                </Button>
              </Grid>
            </Grid>
          </TabPanel>

          {/* TAB 3: AVANÇADO */}
          <TabPanel value={activeTab} index={3}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Nível de Rigor</InputLabel>
                  <Select
                    value={formData.strictness}
                    onChange={(e) => handleChange('strictness', e.target.value)}
                  >
                    <MenuItem value="low">Baixo - Apenas avisar</MenuItem>
                    <MenuItem value="medium">Médio - Sugerir correção</MenuItem>
                    <MenuItem value="high">Alto - Bloquear resposta incorreta</MenuItem>
                  </Select>
                </FormControl>
                <Typography variant="caption" color="textSecondary" display="block" mt={1}>
                  Define o quão restritiva é a validação
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.auto_correct}
                      onChange={(e) => handleChange('auto_correct', e.target.checked)}
                      color="primary"
                    />
                  }
                  label="Auto-correção"
                />
                <Typography variant="caption" color="textSecondary" display="block">
                  Quando ativado, o agente usa a correção sugerida automaticamente
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <Paper style={{ padding: 16, backgroundColor: '#f5f5f5' }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Como funciona:
                  </Typography>
                  <Typography variant="caption" component="div">
                    1. Sistema detecta palavras-gatilho na mensagem<br />
                    2. Extrai entidades configuradas (ex: tipo de serviço, dia da semana)<br />
                    3. Valida se a combinação de entidades existe na base de conhecimento<br />
                    4. Se houver conflito, injeta correção no contexto do agente<br />
                    5. Agente responde com informação correta da base
                  </Typography>
                </Paper>
              </Grid>
            </Grid>
          </TabPanel>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
        <Button onClick={handleSave} color="primary" variant="contained">
          {rule ? 'Atualizar' : 'Criar'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ValidationRuleDialog;
