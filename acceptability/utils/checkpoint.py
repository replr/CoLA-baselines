import torch
import os


class Checkpoint:
    def __init__(self, trainer):
        self.args = trainer.args
        self.trainer = trainer
        self.experiment_ckpt_path = os.path.join(self.args.save_loc,
                                                 self.args.experiment_name + ".ckpt")
        self.final_model_path = os.path.join(self.args.save_loc,
                                             self.args.experiment_name + ".pth")
        self.embedding_path = os.path.join(self.args.save_loc,
                                           self.args.experiment_name + ".emb")

    def load_state_dict(self):
        # First check if resume arg has been passed
        if self.args.resume_file and os.path.exists(self.args.resume_file):
            self._load(self.args.resume_file)

        # Then check if current experiement has a checkpoint
        elif self.args.resume and os.path.exists(self.experiment_ckpt_path):
            self._load(self.experiment_ckpt_path)

            # Try loading embedding
            if os.path.exists(self.embedding_path):
                self.trainer.embedding = torch.load(self.embedding_path)
            elif hasattr(self.args, 'embedding_path') and self.args.embedding_path \
                and os.path.exists(self.args.embedding_path):
                self.trainer.embedding = torch.load(self.args.embedding_path)

    def _load(self, file):
        print("Loading checkpoint")

        loaded = torch.load(file)
        model = self._get_model()

        model.load_state_dict(loaded['model'])
        self.trainer.optimizer.load_state_dict(loaded['optimizer'])
        self.trainer.current_epoch = loaded['current_epoch']
        self.trainer.early_stopping.best_monitored_metric = loaded['best_metric']
        self.trainer.early_stopping.best_monitored_epoch = loaded['best_epoch']
        self.trainer.early_stopping.other_metrics = loaded['other_metrics']

        print("Checkpoint loaded")


    def save(self):
        if not os.path.exists(os.path.dirname(self.experiment_ckpt_path)):
            os.mkdir(os.path.dirname(self.experiment_ckpt_path))

        model = self._get_model()

        save = {
            'model': model.state_dict(),
            'optimizer': self.trainer.optimizer.state_dict(),
            'current_epoch': self.trainer.current_epoch,
            'best_metric': self.trainer.early_stopping.best_monitored_metric,
            'best_epoch': self.trainer.early_stopping.best_monitored_epoch,
            'other_metrics': self.trainer.early_stopping.other_metrics
        }

        torch.save(save, self.experiment_ckpt_path)
        self.save_embedding()

    def restore(self):
        model = self._get_model()

        if os.path.exists(self.experiment_ckpt_path):
            model.load_state_dict(torch.load(self.experiment_ckpt_path)['model'])

    def _get_model(self):
        if type(self.trainer.model) == torch.nn.DataParallel:
            model = self.trainer.model.module
        else:
            model = self.trainer.model
        return model

    def finalize(self):
        if not os.path.exists(os.path.dirname(self.final_model_path)):
            os.mkdir(os.path.dirname(self.final_model_path))

        model = self._get_model()
        torch.save(model, self.final_model_path)
        self.save_embedding()

    def save_embedding(self):
        if hasattr(self.args, 'glove') and not self.args.glove:
            if not os.path.exists(os.path.dirname(self.embedding_path)):
                os.mkdir(os.path.dirname(self.embedding_path))

            torch.save(self.trainer.embedding, self.embedding_path)
