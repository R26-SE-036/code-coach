public class GenCleanTailIndex006 {
    static int tail(int[] weights) {
        return weights[weights.length - 1];
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
