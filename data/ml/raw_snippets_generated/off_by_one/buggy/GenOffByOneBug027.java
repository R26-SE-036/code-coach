public class GenOffByOneBug027 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "closed";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static int countAbove(int[] sizes, int threshold) {
        int hits = 0;
        for (int i = 0; i <= sizes.length; i++) {
            if (sizes[i] > threshold) {
                hits++;
            }
        }
        return hits;
    }
}
