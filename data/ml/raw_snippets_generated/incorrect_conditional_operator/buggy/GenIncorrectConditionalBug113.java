public class GenIncorrectConditionalBug113 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static boolean matches(boolean verified, boolean valid) {
        if (verified = valid) {
            return true;
        }
        return false;
    }
}
