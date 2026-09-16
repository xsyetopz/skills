use std::{cell::RefCell, rc::Rc, sync::atomic::{AtomicUsize, Ordering}};

fn contract(bad: bool, topic: usize) -> bool {
    match topic {
        1 => { // This API rejects overflow instead of intentionally wrapping.
            let value = if bad { Some(u32::MAX.wrapping_add(1)) } else { u32::MAX.checked_add(1) };
            value.is_none()
        }
        2 => { // Canonical key output must not depend on an admissible arrival order.
            let mut keys=vec![2,1];
            if !bad { keys.sort_unstable(); }
            keys==[1,2]
        }
        3 => { // A one-shot iterator is not a reusable result collection.
            let mut iter=[1,2,3].into_iter();
            let first=iter.by_ref().collect::<Vec<_>>();
            let second=if bad { iter.collect::<Vec<_>>() } else { first.clone() };
            first==[1,2,3] && second==[1,2,3]
        }
        4 => (if bad { "🙂".len() } else { "🙂".chars().count() })==1,
        5 => { // Clone of Rc shares the cell; a value snapshot must copy its contents.
            let owner=Rc::new(RefCell::new(1));
            let snapshot=if bad { Rc::clone(&owner) } else { Rc::new(RefCell::new(*owner.borrow())) };
            *owner.borrow_mut()=2;
            let value=*snapshot.borrow();
            value==1
        }
        6 => { // Retain a logical ID, not an index invalidated by insertion before it.
            let mut ids=vec![11,22]; let old_index=1; let id=ids[old_index];
            ids.insert(0,7);
            let value=if bad {ids[old_index]} else {*ids.iter().find(|&&v|v==id).unwrap()};
            value==22
        }
        7 => { // Legal deterministic interleaving: atomic load/store is not atomic RMW.
            let count=AtomicUsize::new(0);
            if bad {
                let a=count.load(Ordering::Relaxed);let b=count.load(Ordering::Relaxed);
                count.store(a+1,Ordering::Relaxed);count.store(b+1,Ordering::Relaxed);
            } else {count.fetch_add(1,Ordering::Relaxed);count.fetch_add(1,Ordering::Relaxed);}
            count.load(Ordering::Relaxed)==2
        }
        8 => { // Dropping an error is not a successful parse.
            let input="invalid";
            let result=if bad {Ok(input.parse::<u32>().unwrap_or_default())} else {input.parse::<u32>()};
            result.is_err()
        }
        _ => panic!("topic must be 1..8"),
    }
}
fn main() {
    let args=std::env::args().skip(1).collect::<Vec<_>>();
    assert!(args.len()==2 && matches!(args[0].as_str(),"red"|"green"),"usage: red|green TOPIC");
    let topic=args[1].parse::<usize>().expect("integer topic");
    let pass=contract(args[0]=="red",topic);
    println!("CONTRACT topic {topic}: {}",if pass {"PASS"} else {"FAIL"});
    if !pass {std::process::exit(1);}
}
