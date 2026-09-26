// Candidate: `declare` narrows the type without emitting a field.
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
  declare resident: Dog;
}

export function run(): string {
  const house = new DogHouse({ name: "Rex", breed: "lab" } as Dog);
  return String(house.resident?.breed);
}
