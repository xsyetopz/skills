// Baseline: the subclass redeclares an inherited field to narrow its type.
// With define semantics (target >= ES2022) the redeclaration re-initializes
// the field to undefined after super() returns.
interface Animal {
  name: string;
}
interface Dog extends Animal {
  breed: string;
}

class House {
  resident: Animal;
  constructor(animal: Animal) {
    this.resident = animal;
  }
}

class DogHouse extends House {
  resident!: Dog;
}

export function run(): string {
  const house = new DogHouse({ name: "Rex", breed: "lab" } as Dog);
  return String(house.resident?.breed);
}
