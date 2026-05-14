# Cambricon MLU370 BANG C 编译脚本
# Usage:
#   make          - 根据 config 编译指定 .mlu 文件
#   make all      - 编译所有 .mlu 文件
#   make check    - 检查 MLU 环境
#   make clean    - 清理编译产物

NEUWARE_HOME ?= /usr/local/neuware
CNCC := $(NEUWARE_HOME)/bin/cncc
ARCH := mtp_372

SRCS := $(wildcard *.mlu)
OBJS := $(SRCS:.mlu=.o)

# 从 config 文件读取要编译的题目
ifneq (,$(wildcard config))
TARGETS := $(shell grep -v '^#' config | grep -v '^$$' | while read line; do \
	for f in *.mlu; do \
		base=$$(echo $$f | sed 's/\.mlu$$//'); \
		num=$$(echo $$base | grep -oP '^\d+' || echo ""); \
		if [ "$$num" = "$$line" ]; then echo "$$f"; fi; \
	done; \
done)
else
TARGETS := $(SRCS)
endif

CNCC_FLAGS := --bang-mlu-arch=$(ARCH) -c -O3

.PHONY: all compile check clean

# 默认目标: 根据 config 编译
compile: $(TARGETS:.mlu=.o)
	@echo "Done."

# 编译所有 .mlu 文件 (忽略 config)
all: $(OBJS)

%.o: %.mlu
	@echo "Compiling $< ..."
	$(CNCC) $< -o $@ $(CNCC_FLAGS)

check:
	@echo "=== MLU 环境检查 ==="
	@echo -n "NEUWARE_HOME: " && echo $(NEUWARE_HOME)
	@if [ -x "$(CNCC)" ]; then \
		echo "cncc:     $(CNCC) [OK]"; \
		$(CNCC) --version 2>/dev/null || true; \
	else \
		echo "cncc:     NOT FOUND [请设置 NEUWARE_HOME]"; \
	fi
	@echo -n "MLU device: " && \
		python3 -c "import torch; import torch_mlu; print(torch.mlu.device_count(), 'card(s)')" 2>/dev/null || \
		echo "检测失败 (torch_mlu 未安装?)"

clean:
	rm -f *.o

.DEFAULT_GOAL := compile
