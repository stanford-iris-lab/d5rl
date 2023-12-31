from typing import Optional, Sequence, Callable

import distrax
import flax.linen as nn
import jax.numpy as jnp

from jaxrl2.networks.kitchen_networks import MLP, MLPRepeatPerLayer ###===### ###---###
from jaxrl2.networks.kitchen_networks.constants import default_init, xavier_init

class NormalPolicy(nn.Module):
    hidden_dims: Sequence[int]
    action_dim: int
    dropout_rate: Optional[float] = None
    std: Optional[float] = 1.
    init_scale: Optional[float] = 1.
    output_scale: Optional[float] = 1.
    init_method: str = 'default'

    @nn.compact
    def __call__(self,
                 observations: jnp.ndarray,
                 training: bool = False):
        outputs = MLP(self.hidden_dims,
                      activate_final=True,
                      dropout_rate=self.dropout_rate,
                      init_scale = self.init_scale
                      )(observations, training=training)

        if self.init_method == 'xavier':
            print('fc layer {}x{}'.format(outputs.shape, self.action_dim))
            means = nn.Dense(self.action_dim, kernel_init=xavier_init())(outputs)
        else:
            means = nn.Dense(self.action_dim, kernel_init=default_init(1e-2))(outputs)

        means *= self.output_scale

        return distrax.MultivariateNormalDiag(loc=means, scale_diag=jnp.ones_like(means)*self.std)


class UnitStdNormalPolicy(nn.Module):
    hidden_dims: Sequence[int]
    action_dim: int
    dropout_rate: Optional[float] = None
    apply_tanh: bool = True
    activations: Callable[[jnp.ndarray], jnp.ndarray] = nn.relu

    @nn.compact
    def __call__(
        self, observations: jnp.ndarray, training: bool = False
    ) -> distrax.Distribution:
        # outputs = MLP(
        #     self.hidden_dims,
        #     activate_final=True,
        #     dropout_rate=self.dropout_rate,
        #     activations=self.activations,
        # )(observations, training=training)

        # hidden_dims: Sequence[int]
        # activations: Callable[[jnp.ndarray], jnp.ndarray] = nn.relu
        # activate_final: int = False
        # dropout_rate: Optional[float] = None
        # init_scale: Optional[float] = 1.
        # key_for_repeat='actions'

        outputs = MLPRepeatPerLayer( ###===### ###---###
            self.hidden_dims,
            activations=self.activations,
            activate_final=True,
            dropout_rate=self.dropout_rate,
            key_for_repeat="states",
        )(observations, training=training)

        means = nn.Dense(self.action_dim, kernel_init=default_init())(outputs)

        if self.apply_tanh:
            means = nn.tanh(means)

        return distrax.MultivariateNormalDiag(loc=means, scale_diag=jnp.ones_like(means))
