public class GenOffByOneBug157 {
    static int countAbove(int[] sizes, int threshold) {
        int hits = 0;
        for (int i = 0; i <= sizes.length; i++) {
            if (sizes[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }

    static boolean isEven1(int total) {
        return total % 2 == 0;
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
