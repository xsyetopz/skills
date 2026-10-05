# ECS

Read when the code is entity component system code (Bevy, flecs, Unity Entities) or when you add
behavior to a game or simulation that uses one.

## Contents

- [What ECS Separates](#what-ecs-separates)
- [Recognize It](#recognize-it)
- [Where Code Goes](#where-code-goes)
- [Enforcement](#enforcement)
- [Agent Mistakes](#agent-mistakes)
- [Example](#example)

## What ECS Separates

Bevy: "ECS is a software pattern that involves breaking your program up into Entities, Components,
and Systems. Entities are unique 'things' that are assigned groups of Components, which are then
processed using Systems." <https://docs.rs/bevy_ecs/latest/bevy_ecs/> (version 0.19.1 when read)

Mertens' ECS FAQ: "OOP colocates data with behavior, ECS separates data from behavior";
"Inheritance is a 1st class citizen in OOP, composition is a 1st class citizen in ECS"; "ECS
encourages exposed POD (plain old data) objects".
<https://github.com/SanderMertens/ecs-faq>

Unity Entities: "Unlike GameObjects, entities contain no code: they're units of data that the
systems you create process."
<https://docs.unity3d.com/Packages/com.unity.entities@1.3/manual/concepts-intro.html>

## Recognize It

- Components are plain data types: in Bevy "normal Rust structs. They are data stored in a World".
  The FAQ says components are "generally plain data types and not encapsulated".
- Systems are the behavior. In Bevy they are "normal Rust functions", and the parameter types
  declare the data they access, which lets the scheduler run systems in parallel. The FAQ defines a
  system as "an executable object that is matched with all entities that have a certain set of
  components."
- Global singletons are Resources: "Resource is a special kind of component that does not belong to
  any entity" (time, renderers, audio servers, asset collections).
- Reactions to events are Observers: "systems that watch for a 'trigger' of a specific Event".
- Entities have no class hierarchy; their kind is the set of components attached.

If entities are subclasses with methods, or components carry update logic, the codebase is OOP with
ECS vocabulary. Find the real convention before adding code.

## Where Code Goes

| Need | Owner |
| --- | --- |
| New data on a thing (health, velocity, tag) | A new component, plain data, no behavior |
| New behavior | A system (a function) that queries the components it needs |
| Data shared by the whole world (time, config, input state) | A resource |
| React to a discrete event | An observer or event handler, in the style the codebase already uses |
| A kind of thing (enemy, projectile) | A set of components, spawned the way existing kinds are spawned |

Follow the existing split: how existing components are named and grouped, how systems are
registered and ordered, and which plugin, module, or world setup owns what. The FAQ's rule: "It is
good practice to design components and systems to have a single responsibility."

## Enforcement

The research found no ECS-specific architecture linter and no official Bevy anti-patterns page. In
Bevy the type system helps: a system's parameters declare what it reads and writes, and the
scheduler uses that to parallelize. Run the project's build and tests, and for Rust the usual
compiler and lint checks the repository has. For layering around the ECS (for example, game rules
outside the engine), see `ports-and-layers.md`.

## Agent Mistakes

These follow from the quotes above (inferred as a checklist; no source names them):

- Behavior in components: methods that mutate other state or run per-frame logic. Move it into a
  system.
- An OOP inheritance hierarchy of entities. The FAQ notes inheritance "has well-known problems,
  such as how difficult it can be to refactor a class hierarchy, or how low-level base classes tend
  to accumulate bloat over time." Compose components instead.
- One system doing many jobs. The FAQ asks for single responsibility; split by job. The term "god
  system" is not from any source.
- Global mutable state outside Resources (statics, singletons). Use a resource.
- Encapsulating component fields behind getters in a codebase that exposes plain data.
- Ignoring the existing component and system split, naming, and registration order.
- Adding ECS to a non-ECS codebase, or object-style code to an ECS one. Do not introduce a second
  architecture.

## Example

Bevy-style data and behavior, separated (Rust sketch; check signatures against the Bevy version the
project pins):

```rust
use bevy::prelude::*;

#[derive(Component)]
struct Health(f32);

#[derive(Component)]
struct Poisoned { damage_per_second: f32 }

// Behavior is a plain function; its parameters declare what it touches.
fn poison_system(time: Res<Time>, mut query: Query<(&Poisoned, &mut Health)>) {
    for (poison, mut health) in &mut query {
        health.0 -= poison.damage_per_second * time.delta_secs();
    }
}
```

Adding the poison effect meant one new component and one new system. No existing type was edited.
