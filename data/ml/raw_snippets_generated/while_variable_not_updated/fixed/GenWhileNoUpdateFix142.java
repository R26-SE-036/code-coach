public class GenWhileNoUpdateFix142 {
    static void pump(boolean ready, int count) {
        while (!ready) {
            System.out.println(count);
            count++;
            ready = count > 10;
        }
    }
}
