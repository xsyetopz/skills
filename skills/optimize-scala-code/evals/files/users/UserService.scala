package users

import scala.concurrent.{ExecutionContext, Future}
import scala.concurrent.ExecutionContext.Implicits.global

object UserService:
  /** Loads users in the order of `ids`; fails with the DAO's exception if any load fails. */
  def loadAll(ids: Seq[Long]): Future[Seq[User]] =
    Future.traverse(ids)(id => Future(Dao.load(id)))

  /** CPU-bound scoring that shares the same pool today. */
  def score(users: Seq[User]): Future[Int] =
    Future(users.map(_.name.hashCode & 0xff).sum)
