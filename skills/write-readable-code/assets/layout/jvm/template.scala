package com.example.component

import scala.collection.immutable.*

object Constants:
  val PublicValue = 1
  private val PrivateValue = 2

class PublicType:
  def publicMethod(): Unit = ()
  protected def protectedMethod(): Unit = ()
  private def privateMethod(): Unit = ()

private[component] class PackageScopedType
private[example] class WiderPackageScopedType

// Keep companion object adjacent to its class.
object PublicType:
  def apply(): PublicType = new PublicType()
