import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Initialize figure
fig, ax = plt.subplots(figsize=(12, 6), dpi=300)
ax.axis('off')

# Title
plt.text(0.5, 0.95, 'The Logic-Chain Mutator Pipeline', ha='center', va='center', 
         fontsize=20, fontweight='bold', color='#2c3e50')

# ==========================================
# LEFT: Inputs (Seeds & Strategies)
# ==========================================
# Context Seeds Box
ax.add_patch(patches.FancyBboxPatch((0.05, 0.6), 0.22, 0.15, boxstyle="round,pad=0.02", 
                                    facecolor='#ecf0f1', edgecolor='#34495e', linewidth=2))
plt.text(0.16, 0.7, 'Context Seeds', ha='center', va='center', fontsize=12, fontweight='bold', color='#2c3e50')
plt.text(0.16, 0.65, '(Benign Logs, Emails)', ha='center', va='center', fontsize=10, color='#7f8c8d')

# Disguise Strategies Box
ax.add_patch(patches.FancyBboxPatch((0.05, 0.25), 0.22, 0.15, boxstyle="round,pad=0.02", 
                                    facecolor='#ecf0f1', edgecolor='#34495e', linewidth=2))
plt.text(0.16, 0.35, 'Disguise Strategies', ha='center', va='center', fontsize=12, fontweight='bold', color='#2c3e50')
plt.text(0.16, 0.3, '(GDPR Purge, OOM Error)', ha='center', va='center', fontsize=10, color='#7f8c8d')

# Arrows from Inputs to Engine
plt.arrow(0.27, 0.675, 0.08, -0.12, head_width=0.02, head_length=0.03, fc='#95a5a6', ec='#95a5a6', linewidth=2)
plt.arrow(0.27, 0.325, 0.08, 0.12, head_width=0.02, head_length=0.03, fc='#95a5a6', ec='#95a5a6', linewidth=2)

# ==========================================
# CENTER: Mutation Engine
# ==========================================
# Central LLM Engine Box
ax.add_patch(patches.FancyBboxPatch((0.38, 0.35), 0.28, 0.3, boxstyle="round,pad=0.05", 
                                    facecolor='#3498db', edgecolor='#2980b9', linewidth=2))
plt.text(0.52, 0.55, 'LLM Mutation Engine', ha='center', va='center', fontsize=14, fontweight='bold', color='white')
plt.text(0.52, 0.48, '[Red Team Persona]', ha='center', va='center', fontsize=11, style='italic', color='#ecf0f1')

# Highlight Action
plt.text(0.52, 0.4, '⚙️ Injects Catastrophic Urgency', ha='center', va='center', 
         fontsize=11, fontweight='bold', color='#f1c40f')

# Arrow from Engine to Output
plt.arrow(0.66, 0.5, 0.12, 0, head_width=0.03, head_length=0.03, fc='#34495e', ec='#34495e', linewidth=3)

# ==========================================
# RIGHT: Poisoned Output
# ==========================================
# Poisoned Payload Box
ax.add_patch(patches.FancyBboxPatch((0.81, 0.4), 0.22, 0.2, boxstyle="round,pad=0.02", 
                                    facecolor='#fadbd8', edgecolor='#c0392b', linewidth=2.5))
plt.text(0.92, 0.53, '☠️ Poisoned Payload', ha='center', va='center', fontsize=12, fontweight='bold', color='#c0392b')
plt.text(0.92, 0.46, '(Context-Aware\nLogic Chain)', ha='center', va='center', fontsize=10, color='#922b21')

plt.tight_layout()
plt.savefig('Mutator_Pipeline.png', bbox_inches='tight')
print("[*] Image generated successfully as 'Mutator_Pipeline.png'")
plt.show()