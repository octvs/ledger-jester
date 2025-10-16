#!/usr/bin/env bash

xan from "$1" | tail +10 >"${1%.xls}.csv"
