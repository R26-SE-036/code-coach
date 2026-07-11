public class GenCleanGeneric067 {
    static String describe1(int quota) {
        if (quota < 100) {
            return "low";
        } else if (quota > 500) {
            return "high";
        }
        return "medium";
    }

    static String join2(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
