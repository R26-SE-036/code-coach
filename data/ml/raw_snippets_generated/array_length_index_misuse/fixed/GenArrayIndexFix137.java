public class GenArrayIndexFix137 {
    static int lastOf(int[] totals) {
        return totals[totals.length - 1];
    }

    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }
}
