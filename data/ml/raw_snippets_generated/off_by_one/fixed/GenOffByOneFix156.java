public class GenOffByOneFix156 {
    static int[] duplicate(int[] sizes) {
        int[] copy = new int[sizes.length];
        for (int i = 0; i < sizes.length; i++) {
            copy[i] = sizes[i];
        }
        return copy;
    }

    static int largest1(int[] sizes) {
        int best = sizes[0];
        for (int i = 1; i < sizes.length; i++) {
            if (sizes[i] > best) {
                best = sizes[i];
            }
        }
        return best;
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
