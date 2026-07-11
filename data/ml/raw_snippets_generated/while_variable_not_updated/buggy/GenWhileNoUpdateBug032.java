public class GenWhileNoUpdateBug032 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "final";
                break;
            default:
                label = "active";
        }
        return label;
    }

    static int gather(int limit, int level) {
        int sum = 0;
        while (limit < level) {
            sum += limit;
        }
        return sum;
    }

    static String status2(int code) {
        String label;
        switch (code) {
            case 1:
                label = "archived";
                break;
            case 2:
                label = "new";
                break;
            default:
                label = "draft";
        }
        return label;
    }
}
