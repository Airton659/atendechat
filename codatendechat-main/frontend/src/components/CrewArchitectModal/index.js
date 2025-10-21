import React, { useState } from "react";
import * as Yup from "yup";
import { Formik, Form, Field } from "formik";
import { toast } from "react-toastify";
import { makeStyles } from "@material-ui/core/styles";
import { green } from "@material-ui/core/colors";
import {
  Button,
  TextField,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  Paper,
  Divider,
  Chip,
  Box,
} from "@material-ui/core";
import { Stars as AutoAwesomeIcon } from "@material-ui/icons";

import { i18n } from "../../translate/i18n";
import api from "../../services/api";
import toastError from "../../errors/toastError";

const useStyles = makeStyles((theme) => ({
  root: {
    display: "flex",
    flexWrap: "wrap",
  },
  textField: {
    marginRight: theme.spacing(1),
    flex: 1,
  },
  btnWrapper: {
    position: "relative",
  },
  buttonProgress: {
    color: green[500],
    position: "absolute",
    top: "50%",
    left: "50%",
    marginTop: -12,
    marginLeft: -12,
  },
  resultPaper: {
    padding: theme.spacing(2),
    marginTop: theme.spacing(2),
    backgroundColor: theme.palette.background.default,
  },
  agentChip: {
    margin: theme.spacing(0.5),
  },
}));

const ArchitectSchema = Yup.object().shape({
  businessDescription: Yup.string()
    .min(20, "Descrição muito curta (mínimo 20 caracteres)")
    .max(1000, "Descrição muito longa (máximo 1000 caracteres)")
    .required("Descrição do negócio é obrigatória"),
  teamName: Yup.string()
    .min(2, "Nome muito curto")
    .max(100, "Nome muito longo")
    .required("Nome da equipe é obrigatório"),
  industry: Yup.string()
    .required("Indústria é obrigatória"),
});

const industries = [
  { value: "ecommerce", label: "E-commerce" },
  { value: "services", label: "Serviços" },
  { value: "technology", label: "Tecnologia" },
  { value: "health", label: "Saúde" },
  { value: "education", label: "Educação" },
  { value: "finance", label: "Finanças" },
  { value: "retail", label: "Varejo" },
  { value: "real_estate", label: "Imobiliário" },
  { value: "other", label: "Outro" },
];

const CrewArchitectModal = ({ open, onClose }) => {
  const classes = useStyles();
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState(null);

  const initialValues = {
    businessDescription: "",
    teamName: "",
    industry: "",
  };

  const handleClose = () => {
    setResult(null);
    onClose();
  };

  const handleGenerate = async (values) => {
    setGenerating(true);
    try {
      const { data } = await api.post("/crews/generate", values);
      setResult(data);
      toast.success("Equipe gerada com sucesso!");
    } catch (err) {
      toastError(err);
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveGenerated = () => {
    toast.success(i18n.t("crews.toasts.created"));
    handleClose();
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
        <Box display="flex" alignItems="center" gap={1}>
          <AutoAwesomeIcon />
          <span>{i18n.t("crews.architect.title")}</span>
        </Box>
      </DialogTitle>
      <Formik
        initialValues={initialValues}
        validationSchema={ArchitectSchema}
        onSubmit={(values) => {
          handleGenerate(values);
        }}
      >
        {({ touched, errors, isSubmitting, values }) => (
          <Form>
            <DialogContent dividers>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                {i18n.t("crews.architect.description")}
              </Typography>

              <div className={classes.root} style={{ marginTop: 16 }}>
                <Field
                  as={TextField}
                  label={i18n.t("crews.architect.teamName")}
                  autoFocus
                  name="teamName"
                  error={touched.teamName && Boolean(errors.teamName)}
                  helperText={touched.teamName && errors.teamName}
                  variant="outlined"
                  margin="dense"
                  fullWidth
                  className={classes.textField}
                />
              </div>

              <div className={classes.root}>
                <FormControl
                  variant="outlined"
                  margin="dense"
                  fullWidth
                  error={touched.industry && Boolean(errors.industry)}
                >
                  <InputLabel>{i18n.t("crews.architect.industry")}</InputLabel>
                  <Field
                    as={Select}
                    name="industry"
                    label={i18n.t("crews.architect.industry")}
                  >
                    {industries.map((ind) => (
                      <MenuItem key={ind.value} value={ind.value}>
                        {ind.label}
                      </MenuItem>
                    ))}
                  </Field>
                </FormControl>
              </div>

              <div className={classes.root}>
                <Field
                  as={TextField}
                  label={i18n.t("crews.architect.businessDescription")}
                  name="businessDescription"
                  error={
                    touched.businessDescription &&
                    Boolean(errors.businessDescription)
                  }
                  helperText={
                    touched.businessDescription && errors.businessDescription
                  }
                  variant="outlined"
                  margin="dense"
                  multiline
                  rows={6}
                  fullWidth
                  className={classes.textField}
                  placeholder={i18n.t("crews.architect.placeholder")}
                />
              </div>

              {result && (
                <Paper className={classes.resultPaper} elevation={0}>
                  <Typography variant="h6" gutterBottom>
                    {i18n.t("crews.architect.result")}
                  </Typography>
                  <Divider style={{ marginBottom: 16 }} />

                  <Typography variant="subtitle2" gutterBottom>
                    {i18n.t("crews.architect.analysis")}
                  </Typography>
                  <Typography variant="body2" paragraph>
                    {result.analysis?.summary || "Análise não disponível"}
                  </Typography>

                  <Typography variant="subtitle2" gutterBottom>
                    {i18n.t("crews.architect.agents")}
                  </Typography>
                  <Box mb={2}>
                    {result.blueprint?.agents?.map((agent, idx) => (
                      <Chip
                        key={idx}
                        label={agent.name}
                        className={classes.agentChip}
                        color="primary"
                        variant="outlined"
                      />
                    ))}
                  </Box>

                  <Typography variant="caption" color="textSecondary">
                    {i18n.t("crews.architect.saved")}
                  </Typography>
                </Paper>
              )}
            </DialogContent>
            <DialogActions>
              {!result ? (
                <>
                  <Button
                    onClick={handleClose}
                    color="secondary"
                    disabled={generating}
                    variant="outlined"
                  >
                    {i18n.t("crews.buttons.cancel")}
                  </Button>
                  <div className={classes.btnWrapper}>
                    <Button
                      type="submit"
                      color="primary"
                      disabled={generating}
                      variant="contained"
                      startIcon={<AutoAwesomeIcon />}
                    >
                      {i18n.t("crews.architect.generate")}
                    </Button>
                    {generating && (
                      <CircularProgress
                        size={24}
                        className={classes.buttonProgress}
                      />
                    )}
                  </div>
                </>
              ) : (
                <Button
                  onClick={handleSaveGenerated}
                  color="primary"
                  variant="contained"
                >
                  {i18n.t("crews.buttons.close")}
                </Button>
              )}
            </DialogActions>
          </Form>
        )}
      </Formik>
    </Dialog>
  );
};

export default CrewArchitectModal;
