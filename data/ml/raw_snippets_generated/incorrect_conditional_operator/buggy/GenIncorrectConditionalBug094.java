public class GenIncorrectConditionalBug094 {
    static boolean matches(boolean loaded, boolean verified) {
        if (loaded = verified) {
            return true;
        }
        return false;
    }

    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
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
