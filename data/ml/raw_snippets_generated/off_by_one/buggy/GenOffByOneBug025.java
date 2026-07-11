public class GenOffByOneBug025 {
    static String join1(String[] parts) {
        StringBuilder builder = new StringBuilder();
        for (int i = 0; i < parts.length; i++) {
            builder.append(parts[i]);
            builder.append(",");
        }
        return builder.toString();
    }

    static void printAll2(int[] scores) {
        for (int value : scores) {
            System.out.println(value);
        }
    }

    static int countAbove(int[] totals, int threshold) {
        int hits = 0;
        for (int i = 0; i <= totals.length; i++) {
            if (totals[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
