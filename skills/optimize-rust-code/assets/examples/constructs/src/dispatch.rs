//! Dispatch constructs: trait objects versus monomorphized generics and
//! enum dispatch. Same shapes, same areas, different call mechanics.

pub trait Shape {
    fn area(&self) -> u64;
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Square(pub u64);

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct Rect(pub u64, pub u64);

impl Shape for Square {
    fn area(&self) -> u64 {
        self.0 * self.0
    }
}

impl Shape for Rect {
    fn area(&self) -> u64 {
        self.0 * self.1
    }
}

// --- baseline: one Box per element, one indirect call per element --------

pub fn boxed_squares(sides: &[u64]) -> Vec<Box<dyn Shape>> {
    sides
        .iter()
        .map(|&s| Box::new(Square(s)) as Box<dyn Shape>)
        .collect()
}

#[unsafe(no_mangle)]
pub fn total_dyn_baseline(shapes: &[Box<dyn Shape>]) -> u64 {
    shapes.iter().map(|shape| shape.area()).sum()
}

// --- candidate 1: generic over a homogeneous slice ----------------------

pub fn total_generic<S: Shape>(shapes: &[S]) -> u64 {
    shapes.iter().map(Shape::area).sum()
}

/// Non-generic wrapper so the monomorphized copy has a symbol to inspect.
#[unsafe(no_mangle)]
pub fn total_generic_candidate(shapes: &[Square]) -> u64 {
    total_generic(shapes)
}

// --- candidate 2: enum dispatch for a closed heterogeneous set ----------

#[derive(Clone, Copy, Debug, PartialEq)]
pub enum AnyShape {
    Square(Square),
    Rect(Rect),
}

impl Shape for AnyShape {
    fn area(&self) -> u64 {
        match self {
            AnyShape::Square(s) => s.area(),
            AnyShape::Rect(r) => r.area(),
        }
    }
}

pub fn boxed_mixed(sides: &[u64]) -> Vec<Box<dyn Shape>> {
    sides
        .iter()
        .map(|&s| -> Box<dyn Shape> {
            if s % 2 == 0 {
                Box::new(Square(s))
            } else {
                Box::new(Rect(s, s + 1))
            }
        })
        .collect()
}

pub fn enum_mixed(sides: &[u64]) -> Vec<AnyShape> {
    sides
        .iter()
        .map(|&s| {
            if s % 2 == 0 {
                AnyShape::Square(Square(s))
            } else {
                AnyShape::Rect(Rect(s, s + 1))
            }
        })
        .collect()
}

#[unsafe(no_mangle)]
pub fn total_enum_candidate(shapes: &[AnyShape]) -> u64 {
    shapes.iter().map(Shape::area).sum()
}
