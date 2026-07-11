public class GenArrayIndexBug078 {
    static int average1(int total, int count) {
        if (count != 0) {
            return total / count;
        }
        return 0;
    }

    static int sum2(int[] ages) {
        int total = 0;
        for (int i = 0; i < ages.length; i++) {
            total += ages[i];
        }
        return total;
    }

    static void showLast(int[] weights) {
        System.out.println(weights[weights.length]);
    }

    static String status3(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "closed";
        }
        return label;
    }
}
