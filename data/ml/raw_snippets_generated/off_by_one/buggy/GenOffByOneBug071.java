public class GenOffByOneBug071 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "new";
                break;
            case 2:
                label = "draft";
                break;
            default:
                label = "paid";
        }
        return label;
    }

    static int addUp(int[] ages) {
        int total = 0;
        for (int i = 0; i <= ages.length; i++) {
            total += ages[i];
        }
        return total;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "paid";
                break;
            default:
                label = "expired";
        }
        return label;
    }
}
