public class GenWhileNoUpdateBug088 {
    static String status1(int code) {
        String label;
        switch (code) {
            case 1:
                label = "draft";
                break;
            case 2:
                label = "active";
                break;
            default:
                label = "expired";
        }
        return label;
    }

    static void pump(boolean armed, int stock) {
        while (!armed) {
            System.out.println(stock);
            stock++;
        }
    }
}
