# Q-Learning in a Grid World

## Introduction

The goal of this project work is to implement the Q-learning algorithm, in the tabular sense, in grid world consisting which simulates in a roughly way a warehouse with walls, two agents, three packages and a delivey station.

Q-learning is a reinforcement learning algorithm that trains one or more agents to assign values to its possible actions based on its current state, without requiring a model of the environment.
The first theoretical step is to write Bellman's optimality equation with respect to the optimal action value function: 
$$Q^\circ(x, u) = r(x, u) + \gamma \sum_{x'\in X} \varphi(x' | x, u) \max_{u'} Q^\circ(x', u')$$

Where:
- $X$ is the state space.
- $U$ is the action space.
- $r(x, u)$ is the instant reward at the current istant.
- $\varphi(x' | x, u)$ is the Markov transition density. Its a probability density function that express the probability to transition from state x to the next state x' when u action is provided.
- $Q^\circ(x, u)$ is the optimal action-value function.

Note that this formula calculates the expected value of a maximum and is therefore suitable for sample implementation.

Working with a grid the following assumptions apply:
- $X$ of finite and discrete size.
- $U$ of finite and discrete size.

Then, having sufficient memory and given the hypothesis, the optimal action value function can be represented as a matrix which links every pair action-value. The matrix has rows equal to the number of states and columns equal to the number of actions.

$$\hat{Q}_{t+1}(x(t), u(t)) = r(t) + \gamma \max_{u'} Q_t(x(t+1), u')$$

$$Q_{t+1}(x(t), u(t)) = Q_t(x(t), u(t)) + \alpha(t)[\hat{Q}_{t+1}(x(t), u(t)) - Q_t(x(t), u(t))]$$

## Implementation

(fai vedere la grid, direi 8x8)