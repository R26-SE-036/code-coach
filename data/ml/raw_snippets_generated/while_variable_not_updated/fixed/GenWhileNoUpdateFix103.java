public class GenWhileNoUpdateFix103 {
    static void pump(boolean armed, int quota) {
        while (!armed) {
            System.out.println(quota);
            quota++;
            armed = quota > 10;
        }
    }
}
