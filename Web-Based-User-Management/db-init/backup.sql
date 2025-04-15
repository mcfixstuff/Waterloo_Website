--
-- PostgreSQL database dump
--

-- Dumped from database version 14.16 (Homebrew)
-- Dumped by pg_dump version 14.16 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: academic_requests; Type: TABLE; Schema: public; Owner: flaskuser
--

CREATE TABLE public.academic_requests (
    id integer NOT NULL,
    email character varying(120) NOT NULL,
    form_type integer NOT NULL,
    data json NOT NULL,
    status character varying(20),
    created_at timestamp without time zone
);


ALTER TABLE public.academic_requests OWNER TO flaskuser;

--
-- Name: academic_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: flaskuser
--

CREATE SEQUENCE public.academic_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.academic_requests_id_seq OWNER TO flaskuser;

--
-- Name: academic_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: flaskuser
--

ALTER SEQUENCE public.academic_requests_id_seq OWNED BY public.academic_requests.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: flaskuser
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO flaskuser;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: flaskuser
--

CREATE SEQUENCE public.users_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_user_id_seq OWNER TO flaskuser;

--
-- Name: users; Type: TABLE; Schema: public; Owner: flaskuser
--

CREATE TABLE public.users (
    email character varying(100) NOT NULL,
    display_name character varying(120) NOT NULL,
    role character varying(50),
    status character varying(50),
    user_id integer DEFAULT nextval('public.users_user_id_seq'::regclass) NOT NULL
);


ALTER TABLE public.users OWNER TO flaskuser;

--
-- Name: academic_requests id; Type: DEFAULT; Schema: public; Owner: flaskuser
--

ALTER TABLE ONLY public.academic_requests ALTER COLUMN id SET DEFAULT nextval('public.academic_requests_id_seq'::regclass);


--
-- Data for Name: academic_requests; Type: TABLE DATA; Schema: public; Owner: flaskuser
--

COPY public.academic_requests (id, email, form_type, data, status, created_at) FROM stdin;
1	eesenvar@CougarNet.UH.EDU	1	{"student_name": "Senvardarli, Egemen E", "student_id": "281281", "degree": "Masters", "graduation_date": "09/2424", "special_request_option": "Full Record Hold", "other_option_detail": "", "justification": "123asd", "signature": "Screenshot_2025-03-18_at_11.28.21.png"}	under_review	2025-03-18 20:06:28.541954
2	eesenvar@CougarNet.UH.EDU	1	{"student_name": "Senvardarli, Egemen E", "student_id": "asasdasd", "degree": "Masters", "graduation_date": "2145", "special_request_option": "Additional Embargo Extension", "other_option_detail": "", "justification": "assdasda", "signature": "Screenshot_2025-03-18_at_11.04.31.png"}	draft	2025-03-18 20:06:47.869451
4	eesenvar@CougarNet.UH.EDU	1	{"student_name": "Senvardarli, Egemen E", "student_id": "21234", "degree": "Masters", "graduation_date": "09/2424", "special_request_option": "Full Record Hold", "other_option_detail": "", "justification": "123124sad", "date": "04-02-2025", "signature": "Screenshot_2025-02-20_at_1.27.08_PM.png"}	draft	2025-04-02 23:29:00.19668
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: flaskuser
--

COPY public.alembic_version (version_num) FROM stdin;
bc2b64947cf2
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: flaskuser
--

COPY public.users (email, display_name, role, status, user_id) FROM stdin;
tez@hotmail.com	not test user pt24	Admin	inactive	4
a1@gmail.com	a2	Admin	inactive	6
hkliu@cougarnet.uh.edu	Hung Liu	Admin	active	7
asd@fas.com	asda	Admin	inactive	10
asd@fasd.com	test	User	inactive	12
awelsaa3@cougarnet.uh.edu	Ash	User	inactive	13
eesenvar@cougarnet.uh.edu	Egemen Erkin Senvardarli	User	active	11
\.


--
-- Name: academic_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: flaskuser
--

SELECT pg_catalog.setval('public.academic_requests_id_seq', 4, true);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: flaskuser
--

SELECT pg_catalog.setval('public.users_user_id_seq', 13, true);


--
-- Name: academic_requests academic_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: flaskuser
--

ALTER TABLE ONLY public.academic_requests
    ADD CONSTRAINT academic_requests_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: flaskuser
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: flaskuser
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: egemen
--

GRANT USAGE ON SCHEMA public TO flaskuser;


--
-- PostgreSQL database dump complete
--

