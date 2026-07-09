#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# generate_loader_activation.py
# 作者: 鸿渚 | 蓝域星河
# 版权: © 2026 鸿渚 - 蓝域星河. All rights reserved.

"""
加载器激活码生成工具（纯 bcrypt，无版本绑定）

功能：
1. 生成免费版/专业版/试用版激活码
2. 自动保存哈希到 activation_keys.json
3. 支持批量生成和列表查看
4. 支持有效期设置
5. 支持删除激活码
"""
import bcrypt
import json
import os
import random
import string
import argparse
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_KEYS_FILE = os.path.join(os.getcwd(), "data", "activation_keys.json")


def format_key(raw_key: str) -> str:
    return raw_key.replace('-', '').replace(' ', '').upper()


def generate_random_key() -> str:
    chars = string.ascii_uppercase + string.digits
    return '-'.join(''.join(random.choices(chars, k=5)) for _ in range(5))


def generate_hash(key: str) -> str:
    formatted = format_key(key)
    hashed = bcrypt.hashpw(formatted.encode('utf-8'), bcrypt.gensalt(rounds=12))
    return hashed.decode('utf-8')


def load_keys_data(file_path: str) -> dict:
    if not os.path.exists(file_path):
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_keys_data(file_path: str, data: dict) -> bool:
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False


def generate_activation_code(license_type: str, customer: str = None, 
                             expires_days: int = None, batch: int = 1,
                             keys_file: str = DEFAULT_KEYS_FILE) -> list:
    results = []
    keys_data = load_keys_data(keys_file)
    
    for i in range(batch):
        key = generate_random_key()
        hashed = generate_hash(key)
        
        customer_id = customer or f"BATCH-{i+1:04d}"
        
        expires = None
        if expires_days:
            expires = (datetime.now() + timedelta(days=expires_days)).isoformat()
        elif license_type == "trial":
            expires = (datetime.now() + timedelta(days=30)).isoformat()
        else:
            expires = "2099-12-31T23:59:59"
        
        info = {
            "type": license_type,
            "customer": customer_id,
            "created": datetime.now().isoformat(),
            "expires": expires
        }
        
        keys_data[hashed] = info
        
        results.append({
            "activation_code": key,
            "type": license_type,
            "customer": customer_id,
            "expires": expires,
            "hash": hashed
        })
    
    save_keys_data(keys_file, keys_data)
    return results


def list_codes(keys_file: str = DEFAULT_KEYS_FILE):
    data = load_keys_data(keys_file)
    if not data:
        print("📭 暂无激活码")
        return
    
    print(f"📋 激活码哈希库 ({len(data)} 条):")
    print("=" * 60)
    for idx, (hash_val, info) in enumerate(data.items(), 1):
        print(f"{idx}. 类型: {info.get('type', 'unknown').upper()}")
        print(f"   客户: {info.get('customer', 'unknown')}")
        print(f"   过期: {info.get('expires', '永久')}")
        print(f"   哈希: {hash_val[:24]}...")
        print("   " + "-" * 40)


def delete_code(keys_file: str = DEFAULT_KEYS_FILE, hash_prefix: str = None):
    if not hash_prefix:
        print("❌ 请提供哈希前缀")
        return
    
    data = load_keys_data(keys_file)
    to_delete = []
    for hash_val, info in data.items():
        if hash_val.startswith(hash_prefix):
            to_delete.append(hash_val)
    
    if not to_delete:
        print(f"❌ 未找到匹配的哈希: {hash_prefix}")
        return
    
    print(f"找到 {len(to_delete)} 个匹配的激活码:")
    for h in to_delete:
        print(f"  - {h[:24]}... ({data[h].get('type')})")
    
    confirm = input("确认删除？(y/n): ").strip().lower()
    if confirm == 'y':
        for h in to_delete:
            del data[h]
        save_keys_data(keys_file, data)
        print(f"✅ 已删除 {len(to_delete)} 个激活码")


def main():
    parser = argparse.ArgumentParser(description="加载器激活码生成工具")
    parser.add_argument("--type", "-t", choices=["free", "pro", "trial"], 
                        default="free", help="授权类型")
    parser.add_argument("--customer", "-c", help="客户标识")
    parser.add_argument("--days", "-d", type=int, help="有效期天数")
    parser.add_argument("--batch", "-b", type=int, default=1, help="生成数量")
    parser.add_argument("--output", "-o", default=DEFAULT_KEYS_FILE, 
                        help="哈希库文件路径")
    parser.add_argument("--list", "-l", action="store_true", 
                        help="列出所有已生成的激活码")
    parser.add_argument("--delete", action="store_true",
                        help="删除激活码（配合 --hash-prefix 使用）")
    parser.add_argument("--hash-prefix", help="要删除的哈希前缀")
    
    args = parser.parse_args()
    
    if args.list:
        list_codes(args.output)
        return
    
    if args.delete:
        delete_code(args.output, args.hash_prefix)
        return
    
    print("=" * 60)
    print(f"  加载器激活码生成工具")
    print(f"  类型: {args.type.upper()} | 数量: {args.batch}")
    if args.days:
        print(f"  有效期: {args.days} 天")
    print("=" * 60)
    print()
    
    results = generate_activation_code(
        license_type=args.type,
        customer=args.customer,
        expires_days=args.days,
        batch=args.batch,
        keys_file=args.output
    )
    
    print("✅ 生成成功！")
    print()
    for r in results:
        print(f"🔑 激活码: {r['activation_code']}")
        print(f"   类型: {r['type'].upper()}")
        print(f"   客户: {r['customer']}")
        print(f"   有效期: {r['expires']}")
        print("   " + "-" * 40)
    
    print()
    print(f"📁 哈希已保存到: {args.output}")
    print()
    print("💡 在加载器激活页面输入激活码即可")


if __name__ == "__main__":
    main()
